import pandas as pd
from sqlalchemy import create_engine, text
import json, glob, os
import xml.etree.ElementTree as ET
from core.utils import get_logger

logger = get_logger("Plugin-Input")

def fetch_db(source, last_updated):
    db_type = source.get("type", "").lower()
    db_name = source.get("database")
    table = source.get("table_name")
    w_col = source.get("watermark_col")
    
    url = f"postgresql+psycopg2://{source['user']}:{source['password']}@{source['host']}:{source['port']}/{db_name}" if "postgres" in db_type else f"mysql+pymysql://{source['user']}:{source['password']}@{source['host']}:{source['port']}/{db_name}"
    
    engine = create_engine(url, pool_pre_ping=True)
    query = f"SELECT * FROM {table} WHERE {w_col} > :last_updated" if w_col else f"SELECT * FROM {table}"
    
    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params={"last_updated": last_updated}) if ":last_updated" in query else pd.read_sql(text(query), conn)
    logger.info(f"✅ [{source['name']}] 추출 완료 ({len(df)}건) / 테이블: {table}")
    return df

def get_hr_lookup(global_config):
    conf = next((s for s in global_config.get("sources", []) if s.get("name") == "ueba_mariaDB"), None)
    if not conf: return None
    try:
        hr_df = fetch_db(conf, "1970-01-01 00:00:00")
        if hr_df is not None and not hr_df.empty:
            id_col = 'employee_id' if 'employee_id' in hr_df.columns else ('emp_id' if 'emp_id' in hr_df.columns else hr_df.columns[0])
            name_col = 'name_kr' if 'name_kr' in hr_df.columns else ('emp_name' if 'emp_name' in hr_df.columns else hr_df.columns[1])
            return dict(zip(hr_df[id_col].astype(str), hr_df[name_col].astype(str)))
    except Exception as e: logger.warning(f"⚠️ HR 로드 실패: {e}")
    return None

def fetch_data(source, global_config, last_updated="1970-01-01 00:00:00"):
    source_name = source.get("name")
    try:
        df = None
        if source.get("type") in ["postgres", "mariadb"]: df = fetch_db(source, last_updated)
        elif source.get("type") == "file":
            files = glob.glob(source.get("path", ""))
            
            # ⭐️ 수정된 부분: .log 확장자도 JSON 형식으로 읽도록 추가!
            df_list = []
            for f in files:
                if f.endswith(".json") or f.endswith(".log"):
                    df_list.append(pd.read_json(f, lines=True))
                else:
                    df_list.append(pd.read_csv(f))
                    
            if df_list: df = pd.concat(df_list, ignore_index=True)

        if df is not None and not df.empty:
            hr_lookup = get_hr_lookup(global_config)
            if hr_lookup and "user_id" in df.columns:
                df["emp_name"] = df["user_id"].astype(str).map(hr_lookup).fillna("Unknown_User")
        return df
    except Exception as e:
        logger.error(f"❌ [{source_name}] 수집 에러: {e}")
        return None