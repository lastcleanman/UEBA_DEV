import sys
import os
import json
import importlib
import glob
import time
import argparse
import shutil
from datetime import datetime
from sqlalchemy import create_engine, text
import pandas as pd
import numpy as np

if "/UEBA_DEV" not in sys.path: sys.path.insert(0, "/UEBA_DEV")

from core.utils import get_spark_session, get_logger
logger = get_logger("CoreEngine")

CONFIG_FILE = "/UEBA_DEV/conf/ueba_settings.json"
WATERMARK_FILE = "/UEBA_DEV/conf/watermark.json"

# ⭐️ 단계별 독립 실행을 위한 중간 데이터 저장소
INTERMEDIATE_PATH = "/UEBA_DEV/data/intermediate"
os.makedirs(INTERMEDIATE_PATH, exist_ok=True)

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)

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

def execute_plugins(spark, df, plugin_list, step_name, global_config, source_name=None):
    for path in plugin_list:
        try:
            plugin = importlib.import_module(path)
            if hasattr(plugin, "execute"):
                if step_name == "Process": df = plugin.execute(spark, df, source_name, global_config)
                else: df = plugin.execute(df, global_config)
        except Exception as e: logger.error(f"❌ [{step_name}] {path} 실패: {e}")
    return df

# ==========================================
# 🤖 AI 이상행위 핵심 분석 로직 (ML Intelligence)
# ==========================================
def analyze_behavior(spark, current_df, source_name, config): # ⭐️ 인자 4개 확인
    try:
        # Py4J 에러 회피를 위한 데이터 변환
        rows = current_df.collect()
        if not rows: return current_df
        
        data_list = [row.asDict() for row in rows]
        df = pd.DataFrame(data_list)

        current_hour = datetime.now().hour
        is_night = 1 if 0 <= current_hour <= 5 else 0
        
        user_counts = df.groupby('user').size()
        avg_batch_count = user_counts.mean()
        
        logger.info(f"🤖 [{source_name}] AI 지표 분석 중... (대상: {len(df)}건)")

        def calculate_score(row):
            score = 0
            reasons = []
            
            # 1. 폭증 분석
            user_count = user_counts.get(row['user'], 0)
            if user_count > (avg_batch_count * 3):
                score += 40
                reasons.append(f"행위 폭증({user_count}건)")
            
            # 2. 민감 리소스 분석
            res_val = str(row.get('resource', ''))
            if any(ext in res_val for ext in ['.sql', 'admin', 'backup']):
                score += 50
                reasons.append("민감 경로 접근")
                
            if is_night:
                score += 20
                reasons.append("심야 활동")
                
            return pd.Series([score, ", ".join(reasons)])

        df[['risk_score', 'anomaly_reason']] = df.apply(calculate_score, axis=1)
        
        # ⭐️ DB 저장 로직 (상단 카운트 연동 핵심)
        db_engine = get_db_engine(config)
        anomalies = df[df['risk_score'] >= 70].copy() # 70점 이상만 추출
        
        if not anomalies.empty and db_engine:
            with db_engine.begin() as conn:
                for _, row in anomalies.iterrows():
                    conn.execute(text("""
                        INSERT INTO sj_ueba_anomalies (user, risk_score, anomaly_reason, source_name)
                        VALUES (:u, :s, :r, :src)
                    """), {
                        "u": row['user'], "s": row['risk_score'], 
                        "r": row['anomaly_reason'], "src": source_name
                    })
            logger.warning(f"🚨 [Anomaly Detected & Saved] {len(anomalies)}건 기록됨 ({source_name})")

        return spark.createDataFrame(df)

    except Exception as e:
        logger.error(f"❌ AI 분석 로직 실행 실패: {e}")
        return current_df

# ==========================================
# 🚀 1. 수집 단계 (Input)
# ==========================================
def run_input(config):
    db_engine = get_db_engine(config)
    pipeline = config.get("pipeline", {})
    sources = [s for s in config.get("sources", []) if s.get("enabled", True)]
    input_plugin = importlib.import_module(pipeline.get("input")[0])

    for source in sources:
        start_time = datetime.now()
        source_name = source.get('name')
        watermark_col = source.get("watermark_col", "final_ts")
        out_path = os.path.join(INTERMEDIATE_PATH, f"{source_name}_input.parquet")
        
        try:
            last_ts = get_last_ts(source_name)
            if last_ts == "1970-01-01 00:00:00": last_ts = source.get("watermark_default", "1970-01-01 00:00:00")
                
            raw_pandas_df = input_plugin.fetch_data(source, config, last_updated=last_ts)
            
            if raw_pandas_df is None or raw_pandas_df.dropna(axis=1, how='all').empty:
                logger.info(f"⏩ [{source_name}] 신규 수집 데이터 없음.")
                save_history(db_engine, source_name, 0, "SUCCESS", start_time=start_time)
                if os.path.exists(out_path): os.remove(out_path)
                continue
                
            if watermark_col in raw_pandas_df.columns:
                set_last_ts(source_name, str(raw_pandas_df[watermark_col].max()))
                
            raw_pandas_df.to_parquet(out_path, index=False)
            logger.info(f"✅ [{source_name}] 데이터 수집 및 임시 저장 완료 (Input -> Process 대기)")

        except Exception as e:
            logger.error(f"❌ [{source_name}] Input 에러: {e}")
            save_history(db_engine, source_name, 0, "FAIL", str(e), start_time=start_time)

# ==========================================
# 🛠️ 2. 정제 단계 (Process)
# ==========================================
def run_process(spark, config):
    pipeline = config.get("pipeline", {})
    sources = [s for s in config.get("sources", []) if s.get("enabled", True)]

    for source in sources:
        source_name = source.get('name')
        in_path = os.path.join(INTERMEDIATE_PATH, f"{source_name}_input.parquet")
        out_path = os.path.join(INTERMEDIATE_PATH, f"{source_name}_process.parquet")
        
        if not os.path.exists(in_path):
            logger.warning(f"⚠️ [{source_name}] 수집된 데이터가 없습니다.")
            continue
        
        try:
            raw_pandas_df = pd.read_parquet(in_path)
            dict_list = raw_pandas_df.replace({pd.NA: None}).where(pd.notnull(raw_pandas_df), None).to_dict(orient='records')
            if not dict_list: continue

            spark_df = spark.createDataFrame(dict_list)
            clean_df = execute_plugins(spark, spark_df, pipeline.get("process", []), "Process", config, source_name)
            
            if clean_df.count() > 0:
                clean_df.write.mode("overwrite").parquet(out_path)
                logger.info(f"✅ [{source_name}] 데이터 정제 완료 (Process -> Detection 대기)")
        except Exception as e: logger.error(f"❌ [{source_name}] Process 에러: {e}")

# ==========================================
# 🤖 3. 분석 단계 (Detect: Rule + ML Intelligence)
# ==========================================
def run_detect(spark, config):
    pipeline = config.get("pipeline", {})
    sources = [s for s in config.get("sources", []) if s.get("enabled", True)]

    for source in sources:
        source_name = source.get('name')
        in_path = os.path.join(INTERMEDIATE_PATH, f"{source_name}_process.parquet")
        out_path = os.path.join(INTERMEDIATE_PATH, f"{source_name}_detect.parquet")
        
        if not os.path.exists(in_path): continue
        
        try:
            clean_df = spark.read.parquet(in_path)
            detected_df = execute_plugins(spark, clean_df, pipeline.get("detection", []), "Detection", config)
            
            final_df = analyze_behavior(spark, detected_df, source_name, config)
            
            final_df.write.mode("overwrite").parquet(out_path)
            logger.info(f"✅ [{source_name}] AI 위협 분석 완료")
        except Exception as e: logger.error(f"❌ [{source_name}] Detect 에러: {e}")

# ==========================================
# 💾 4. 적재 단계 (Output: Elastic Load)
# ==========================================
def run_output(spark, config):
    db_engine = get_db_engine(config)
    pipeline = config.get("pipeline", {})
    sources = [s for s in config.get("sources", []) if s.get("enabled", True)]

    for source in sources:
        start_time = datetime.now()
        source_name = source.get('name')
        in_path = os.path.join(INTERMEDIATE_PATH, f"{source_name}_detect.parquet")
        
        if not os.path.exists(in_path):
            logger.warning(f"⚠️ [{source_name}] 적재할 데이터가 없습니다.")
            continue
        
        try:
            detected_df = spark.read.parquet(in_path)
            execute_plugins(spark, detected_df, pipeline.get("output", []), "Output", config)
            
            count = detected_df.count()
            save_history(db_engine, source_name, count, "SUCCESS", start_time=start_time)
            
        except Exception as e: 
            logger.error(f"❌ [{source_name}] Output 에러: {e}")
            save_history(db_engine, source_name, 0, "FAIL", str(e), start_time=start_time)

# ==========================================
# 🎯 메인 실행기 (하이브리드 모드 지원)
# ==========================================
MODE_FILE = "/UEBA_DEV/data/mode.txt"

def get_current_mode():
    try:
        if os.path.exists(MODE_FILE):
            with open(MODE_FILE, "r") as f:
                return f.read().strip().lower()
    except: pass
    return "manual"

def main():
    config = load_config()
    spark = get_spark_session()
    logger.info("🚀 UEBA Enterprise Engine 기동 (Hybrid Mode)")
    
    try:
        last_mode = None
        while True:
            current_mode = get_current_mode()
            
            if current_mode != last_mode:
                logger.info(f"🔄 엔진 모드 변경 감지: [{current_mode.upper()}] 모드로 동작합니다.")
                last_mode = current_mode
                
            if current_mode == "daemon":
                logger.info(f"\n--- 🚀 {datetime.now()} [자동 데몬] 분석 주기 시작 ---")
                config = load_config()
                run_input(config)
                run_process(spark, config)
                run_detect(spark, config)
                run_output(spark, config)
                
                for _ in range(30):
                    if get_current_mode() != "daemon": break
                    time.sleep(1)
                    
            elif current_mode == "manual":
                for step_name in ["all", "input", "rule", "ml", "elastic"]:
                    flag_file = f"/UEBA_DEV/data/trigger_{step_name}.flag"
                    if os.path.exists(flag_file):
                        os.remove(flag_file)
                        logger.info(f"\n--- 🚀 [수동 감지] {step_name.upper()} 단계 실행 ---")
                        config = load_config()
                        
                        if step_name in ["all", "input"]: 
                            run_input(config)
                            run_process(spark, config)
                        if step_name in ["all", "rule", "ml"]: 
                            run_detect(spark, config)
                        if step_name in ["all", "elastic"]: 
                            run_output(config)
                        
                        logger.info(f"✅ {step_name.upper()} 명령 처리 완료.")
                
                time.sleep(1)

    except KeyboardInterrupt: pass
    finally: spark.stop()

if __name__ == "__main__": main()