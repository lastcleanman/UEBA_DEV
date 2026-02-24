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
    
    # ⭐️ 수정: DB 테이블도 기본 워터마크 컬럼을 지정하여 누락 방지
    w_col = source.get("watermark_col", "timestamp") 
    
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

def get_parser_info(source_name, global_config):
    base_dir = global_config.get("system", {}).get("base_dir", "/UEBA_DEV")
    xml_path = os.path.join(base_dir, "conf", "parsers", f"{source_name}.xml")
    
    fmt, sep, columns = "json", ",", None
    if os.path.exists(xml_path):
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            fmt = root.get("format", "json")
            sep = root.get("delimiter", ",")
            if fmt == "delimited":
                # ⭐️ 핵심 수정: 'field' -> './/field' 로 변경하여 내부에 숨은 태그까지 모두 찾습니다.
                fields = sorted(root.findall('.//field'), key=lambda x: int(x.get('index', 0)))
                columns = [f.get('target') for f in fields]
        except Exception as e:
            logger.error(f"❌ XML 파싱 에러({source_name}): {e}")
    return fmt, sep, columns

def fetch_data(source, global_config, last_updated="1970-01-01 00:00:00"):
    source_name = source.get("name")
    try:
        df = None
        if source.get("type") in ["postgres", "mariadb"]: 
            df = fetch_db(source, last_updated)
            
        elif source.get("type") == "file":
            files = glob.glob(source.get("path", ""))
            
            # ⭐️ 동적 파서 정보 로드
            fmt, sep, columns = get_parser_info(source_name, global_config)
            
            df_list = []
            for f in files:
                if fmt == "delimited" and columns:
                    # 정규식 충돌 방지를 위한 특수문자 이스케이프 (| 등)
                    safe_sep = f"\\{sep}" if sep in "|^*." else sep
                    df_list.append(pd.read_csv(f, sep=safe_sep, header=None, names=columns, engine='python', dtype=str))
                elif fmt == "json":
                    df_list.append(pd.read_json(f, lines=True))
                else:
                    df_list.append(pd.read_csv(f))
                    
            if df_list: 
                df = pd.concat(df_list, ignore_index=True)
                
                # 워터마크 (시간) 처리
                w_col = source.get("watermark_col", "timestamp")
                if w_col not in df.columns and "@timestamp" in df.columns: 
                    w_col = "@timestamp"
                    
                if w_col in df.columns:
                    original_count = len(df)
                    
                    # ⭐️ 1. 보이지 않는 공백 및 찌꺼기 문자 완벽 제거
                    df[w_col] = df[w_col].astype(str).str.strip()
                    last_ts_clean = str(last_updated).strip()
                    
                    # ⭐️ 2. 단순 문자열을 실제 시계(Datetime 객체)로 강제 변환
                    # 파싱 실패 시 1970년으로 초기화하여 무조건 수집되도록 방어막 전개
                    df['__parsed_time__'] = pd.to_datetime(df[w_col], errors='coerce').fillna(pd.Timestamp("1970-01-01"))
                    
                    safe_last = pd.to_datetime(last_ts_clean, errors='coerce')
                    if pd.isna(safe_last): 
                        safe_last = pd.Timestamp("1970-01-01")
                        
                    # ⭐️ 3. 실제 시간 크기를 수학적으로 비교하여 최신 데이터만 추출
                    df = df[df['__parsed_time__'] > safe_last]
                    
                    # 임시로 만든 시간 연산용 컬럼 삭제
                    df = df.drop(columns=['__parsed_time__'])
                    
                    if original_count != len(df):
                        logger.info(f"🔍 [{source_name}] 신규 {len(df)}건 추출 완료 (구분자: '{sep}')")

        # HR 조인 
        if df is not None and not df.empty:
            hr_lookup = get_hr_lookup(global_config)
            if hr_lookup and "user_id" in df.columns:
                df["emp_name"] = df["user_id"].astype(str).map(hr_lookup).fillna("Unknown_User")
        return df
    except Exception as e:
        logger.error(f"❌ 수집 에러: {e}")
        return None