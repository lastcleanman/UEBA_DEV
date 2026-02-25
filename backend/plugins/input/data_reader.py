import glob
import pandas as pd
from sqlalchemy import create_engine, text
from backend.core.utils import get_logger

logger = get_logger("Plugin-Input")

def get_db_engine(global_config):
    conf = next((s for s in global_config.get("sources", []) if s.get("name") == "ueba_mariaDB"), None)
    if not conf or not conf.get("enabled"): 
        return None
    url = f"mysql+pymysql://{conf['user']}:{conf['password']}@{conf['host']}:{conf['port']}/{conf['database']}"
    return create_engine(url, pool_pre_ping=True)

def execute(spark, source_config, global_config):
    source_name = source_config.get("name")
    file_path = source_config.get("path") 
    
    logger.info(f"🔍 [{source_name}] 로그 파일 탐색 중... ({file_path})")
    files = glob.glob(file_path) if file_path else []
    
    if not files:
        logger.warning(f"⚠️ [{source_name}] 수집할 파일이 없습니다.")
        return None

    try:
        # 파일 수집 (워터마크 우회하여 전체 수집)
        df_list = [pd.read_csv(f, sep="|", header=None, engine='python', on_bad_lines='skip', dtype=str) for f in files]
        if not df_list: return None
        
        pdf = pd.concat(df_list, ignore_index=True).fillna("")
        row_count = len(pdf)

        # MariaDB 이력 적재
        db_engine = get_db_engine(global_config)
        if db_engine:
            with db_engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO sj_ueba_ingestion_history (source_name, processed_count, status, start_time)
                    VALUES (:name, :count, 'SUCCESS', NOW())
                """), {"name": source_name, "count": row_count})
            logger.info(f"💾 [{source_name}] DB 수집 이력 적재 완료: {row_count}건")
        else:
            logger.warning(f"⚠️ [{source_name}] MariaDB가 비활성화되어 있거나 설정이 없습니다. 이력 적재를 건너뜁니다.")

        return spark.createDataFrame(pdf)

    except Exception as e:
        logger.error(f"❌ [{source_name}] 수집 중 에러: {e}")
        return None