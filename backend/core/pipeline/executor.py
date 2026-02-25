import os
import json
import shutil
import importlib
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text
from backend.core.utils import get_logger, get_spark_session
from backend.core.config import INTERMEDIATE_PATH, WATERMARK_FILE

logger = get_logger("PipelineExecutor")

class PipelineExecutor:
    def __init__(self, config, plugin_manager):
        self.config = config
        self.pm = plugin_manager
        self.db_engine = self._get_db_engine()
        os.makedirs(INTERMEDIATE_PATH, exist_ok=True)

    def _get_db_engine(self):
        conf = next((s for s in self.config.get("sources", []) if s.get("name") == "ueba_mariaDB"), None)
        if not conf: return None
        url = f"mysql+pymysql://{conf['user']}:{conf['password']}@{conf['host']}:{conf['port']}/{conf['database']}"
        return create_engine(url, pool_pre_ping=True)

    def _save_history(self, source, count, status, error="", start_time=None):
        if self.db_engine is None: return
        try:
            with self.db_engine.begin() as conn:
                conn.execute(text("""
                    INSERT INTO sj_ueba_ingestion_history (source_name, processed_count, status, error_message, start_time)
                    VALUES (:s, :c, :st, :e, :t)
                """), {"s": source, "c": count, "st": status, "e": error, "t": start_time})
            logger.info(f"📜 [History] {source} 완료 ({count}건)")
        except Exception as e: logger.warning(f"⚠️ 이력 저장 실패: {e}")

    def _get_last_ts(self, source_name):
        try:
            if os.path.exists(WATERMARK_FILE):
                with open(WATERMARK_FILE, "r") as f: return json.load(f).get(source_name, "1970-01-01 00:00:00")
        except: pass
        return "1970-01-01 00:00:00"

    def _set_last_ts(self, source_name, ts):
        try:
            os.makedirs(os.path.dirname(WATERMARK_FILE), exist_ok=True)
            data = {}
            if os.path.exists(WATERMARK_FILE):
                with open(WATERMARK_FILE, "r") as f:
                    try: data = json.load(f)
                    except: data = {}
            data[source_name] = str(ts)
            with open(WATERMARK_FILE, "w") as f: json.dump(data, f, indent=4)
        except Exception as e: logger.warning(f"⚠️ 워터마크 저장 실패: {e}")

    def run_input(self):
        sources = [s for s in self.config.get("sources", []) if s.get("enabled", True)]
        input_plugins = self.pm.load_plugins("input")
        if not input_plugins: return
        input_plugin = importlib.import_module(input_plugins[0])

        for source in sources:
            start_time = datetime.now()
            source_name = source.get('name')
            watermark_col = source.get("watermark_col", "timestamp")
            out_path = os.path.join(INTERMEDIATE_PATH, f"{source_name}_input.parquet")

            try:
                last_ts = self._get_last_ts(source_name)
                if last_ts == "1970-01-01 00:00:00":
                    last_ts = source.get("watermark_default", "1970-01-01 00:00:00")

                raw_pandas_df = input_plugin.fetch_data(source, self.config, last_updated=last_ts)

                if raw_pandas_df is None or raw_pandas_df.dropna(axis=1, how='all').empty:
                    logger.info(f"⏩ [{source_name}] 신규 수집 데이터 없음")
                    self._save_history(source_name, 0, "SUCCESS", start_time=start_time)
                    for suffix in ["_input.parquet", "_process.parquet", "_detect.parquet"]:
                        ghost_file = os.path.join(INTERMEDIATE_PATH, f"{source_name}{suffix}")
                        if os.path.exists(ghost_file):
                            if os.path.isdir(ghost_file): shutil.rmtree(ghost_file)
                            else: os.remove(ghost_file)
                    continue

                if watermark_col not in raw_pandas_df.columns and '@timestamp' in raw_pandas_df.columns:
                    watermark_col = '@timestamp'

                if watermark_col in raw_pandas_df.columns:
                    new_ts = str(raw_pandas_df[watermark_col].max())
                    self._set_last_ts(source_name, new_ts)
                    logger.info(f"🕒 [{source_name}] 워터마크 갱신 완료: {new_ts}")

                raw_pandas_df.to_parquet(out_path, index=False)
                logger.info(f"✅ [{source_name}] 데이터 수집 완료 ({len(raw_pandas_df)}건)")

            except Exception as e:
                logger.error(f"❌ [{source_name}] Input 에러: {e}")
                self._save_history(source_name, 0, "FAIL", str(e), start_time=start_time)

    def run_process(self, spark):
        sources = [s for s in self.config.get("sources", []) if s.get("enabled", True)]
        for source in sources:
            source_name = source.get('name')
            in_path = os.path.join(INTERMEDIATE_PATH, f"{source_name}_input.parquet")
            out_path = os.path.join(INTERMEDIATE_PATH, f"{source_name}_process.parquet")

            if not os.path.exists(in_path): continue

            try:
                raw_pandas_df = pd.read_parquet(in_path)
                raw_pandas_df = raw_pandas_df.fillna("").astype(str)
                raw_pandas_df = raw_pandas_df.replace({'nan': '', 'None': '', '<NA>': ''})

                dict_list = raw_pandas_df.to_dict(orient='records')
                if not dict_list: continue

                spark_df = spark.createDataFrame(dict_list)
                clean_df = self.pm.execute_plugins(spark, spark_df, "process", source_name)

                if clean_df.count() > 0:
                    clean_df.write.mode("overwrite").parquet(out_path)
                    logger.info(f"✅ [{source_name}] 데이터 정제 완료")
            except Exception as e: logger.error(f"❌ [{source_name}] Process 에러: {e}")

    def run_detect(self, spark):
        sources = [s for s in self.config.get("sources", []) if s.get("enabled", True)]
        for source in sources:
            source_name = source.get('name')
            in_path = os.path.join(INTERMEDIATE_PATH, f"{source_name}_process.parquet")
            out_path = os.path.join(INTERMEDIATE_PATH, f"{source_name}_detect.parquet")

            if not os.path.exists(in_path): continue

            try:
                clean_df = spark.read.parquet(in_path)
                detected_df = self.pm.execute_plugins(spark, clean_df, "detection", source_name)
                detected_df.write.mode("overwrite").parquet(out_path)
                logger.info(f"✅ [{source_name}] AI 위협 분석 완료")
            except Exception as e: logger.error(f"❌ [{source_name}] Detect 에러: {e}")

    def run_output(self, spark):
        sources = [s for s in self.config.get("sources", []) if s.get("enabled", True)]
        for source in sources:
            start_time = datetime.now()
            source_name = source.get('name')
            in_path = os.path.join(INTERMEDIATE_PATH, f"{source_name}_detect.parquet")

            if not os.path.exists(in_path): continue

            try:
                detected_df = spark.read.parquet(in_path)
                self.pm.execute_plugins(spark, detected_df, "output", source_name)
                
                count = detected_df.count()
                self._save_history(source_name, count, "SUCCESS", start_time=start_time)
            except Exception as e:
                self._save_history(source_name, 0, "FAIL", str(e), start_time=start_time)
    
    def execute(self):
        """파이프라인 전체 단계를 순서대로 실행합니다."""
        logger.info("🚀 UEBA 파이프라인 분석을 시작합니다...")
        
        # 1. Spark 세션 생성
        spark = get_spark_session()
        
        try:
            # 2. 단계별 메서드 호출
            logger.info("Step 1: 데이터 수집(Input) 시작")
            self.run_input()
            
            logger.info("Step 2: 데이터 정제(Process) 시작")
            self.run_process(spark)
            
            logger.info("Step 3: 위협 탐지(Detect) 시작")
            self.run_detect(spark)
            
            logger.info("Step 4: 최종 적재(Output) 시작")
            self.run_output(spark)
            
            logger.info("✅ 파이프라인의 모든 단계가 성공적으로 완료되었습니다.")
            
        except Exception as e:
            logger.error(f"⚠️ 파이프라인 실행 중 치명적 에러 발생: {e}")
        finally:
            # 자원 관리를 위해 필요한 경우 세션 처리 로직 추가 가능
            pass