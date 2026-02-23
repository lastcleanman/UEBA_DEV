import sys
import os
import json
import importlib
import glob
import time
from datetime import datetime
from sqlalchemy import create_engine, text
import pandas as pd

if "/UEBA_DEV" not in sys.path: sys.path.insert(0, "/UEBA_DEV")

from core.utils import get_spark_session, get_logger
logger = get_logger("CoreEngine")

CONFIG_FILE = "/UEBA_DEV/conf/ueba_settings.json"
WATERMARK_FILE = "/UEBA_DEV/conf/watermark.json"

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)

# 이력 관리는 HR MariaDB(이름이 ueba_mariaDB인 소스)를 찾아 저장
def get_db_engine(config):
    conf = next((s for s in config.get("sources", []) if s.get("name") == "ueba_mariaDB"), None)
    if not conf: return None
    url = f"mysql+pymysql://{conf['user']}:{conf['password']}@{conf['host']}:{conf['port']}/{conf['database']}"
    return create_engine(url, pool_pre_ping=True)

def save_history(db_engine, source, count, status, error="", start_time=None):
    if db_engine is None: return
    try:
        with db_engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO sj_ueba_ingestion_history (source_name, processed_count, status, error_message, start_time)
                VALUES (:s, :c, :st, :e, :t)
            """), {"s": source, "c": count, "st": status, "e": error, "t": start_time})
        logger.info(f"📜 [History] {source} 완료 ({count}건)")
    except Exception as e: logger.warning(f"⚠️ 이력 저장 실패: {e}")

def get_last_ts(source_name):
    try:
        if os.path.exists(WATERMARK_FILE):
            with open(WATERMARK_FILE, "r") as f: return json.load(f).get(source_name, "1970-01-01 00:00:00")
    except: pass
    return "1970-01-01 00:00:00"

def set_last_ts(source_name, ts):
    try:
        data = {}
        if os.path.exists(WATERMARK_FILE):
            with open(WATERMARK_FILE, "r") as f: data = json.load(f)
        data[source_name] = str(ts)
        with open(WATERMARK_FILE, "w") as f: json.dump(data, f)
    except: pass

# ⭐️ 플러그인 실행 시 global_config를 함께 넘겨줍니다.
def execute_plugins(spark, df, plugin_list, step_name, global_config, source_name=None):
    for path in plugin_list:
        try:
            plugin = importlib.import_module(path)
            if hasattr(plugin, "execute"):
                if step_name == "Process": df = plugin.execute(spark, df, source_name, global_config)
                else: df = plugin.execute(df, global_config)
        except Exception as e: logger.error(f"❌ [{step_name}] {path} 실패: {e}")
    return df

def run_pipeline(spark, config):
    db_engine = get_db_engine(config)
    pipeline = config.get("pipeline", {})
    sources = [s for s in config.get("sources", []) if s.get("enabled", True)]

    input_plugin = importlib.import_module(pipeline.get("input")[0])

    total_processed = 0
    for source in sources:
        start_time = datetime.now()
        source_name = source.get('name')
        watermark_col = source.get("watermark_col", "final_ts")
        
        try:
            last_ts = get_last_ts(source_name)
            if last_ts == "1970-01-01 00:00:00": last_ts = source.get("watermark_default", "1970-01-01 00:00:00")
                
            # 1. Input (수집) - global_config 전달
            raw_pandas_df = input_plugin.fetch_data(source, config, last_updated=last_ts)
            
            if raw_pandas_df is None or raw_pandas_df.dropna(axis=1, how='all').empty:
                logger.info(f"⏩ [{source_name}] 신규 수집 데이터 없음.")
                save_history(db_engine, source_name, 0, "SUCCESS", start_time=start_time)
                continue
                
            new_max_ts = str(raw_pandas_df[watermark_col].max()) if watermark_col in raw_pandas_df.columns else None
            dict_list = raw_pandas_df.replace({pd.NA: None}).where(pd.notnull(raw_pandas_df), None).to_dict(orient='records')
            if not dict_list: continue

            spark_df = spark.createDataFrame(dict_list)

            # 2. Process (정제)
            clean_df = execute_plugins(spark, spark_df, pipeline.get("process", []), "Process", config, source_name)
            if clean_df.count() == 0: continue
            if new_max_ts: set_last_ts(source_name, new_max_ts)

            # 3. Detect (위협 분석)
            detected_df = execute_plugins(spark, clean_df, pipeline.get("detection", []), "Detection", config)
            
            # 4. Output (적재)
            execute_plugins(spark, detected_df, pipeline.get("output", []), "Output", config)
            
            count = detected_df.count()
            save_history(db_engine, source_name, count, "SUCCESS", start_time=start_time)
            total_processed += count

        except Exception as e:
            logger.error(f"❌ [{source_name}] 파이프라인 에러: {e}")
            save_history(db_engine, source_name, 0, "FAIL", str(e), start_time=start_time)

def main():
    config = load_config()
    logger.info("🚀 UEBA Enterprise Engine 가동 (Single-Config Architecture)")
    spark = get_spark_session()
    
    try:
        while True:
            logger.info(f"\n--- {datetime.now()} 수집 주기 시작 ---")
            run_pipeline(spark, load_config()) # 매 주기마다 설정파일 갱신 반영
            time.sleep(30)
    except KeyboardInterrupt: pass
    finally: spark.stop()

if __name__ == "__main__": main()