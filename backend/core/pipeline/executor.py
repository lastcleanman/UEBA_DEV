import sys
sys.path.insert(0, "/UEBA_DEV")

import json
import importlib
import functools
from pyspark.sql import SparkSession, DataFrame
from backend.core.utils import get_logger
from backend.core.config import CONFIG_FILE

logger = get_logger("PipelineExecutor")

class UEBAPipeline:
    def __init__(self):
        self.spark = SparkSession.builder.appName("UEBA_Core_Engine").getOrCreate()
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self.config = json.load(f)
        except Exception as e:
            logger.error(f"❌ 설정 파일 로드 실패: {e}")
            self.config = {}

    def run_pipeline(self):
        logger.info("🚀 UEBA 데이터 파이프라인 가동을 시작합니다.")
        
        try:
            # ---------------------------------------------------------
            # 1단계: 수집 (Input)
            # ---------------------------------------------------------
            logger.info("▶️ [Step 1] 데이터 수집 및 DB 이력 적재 시작")
            input_plugins = self.config.get("pipeline", {}).get("input", [])
            
            collected_data = [] # ⭐️ (소스이름, 데이터프레임) 쌍으로 저장
            for plugin_path in input_plugins:
                plugin_module = importlib.import_module(plugin_path)
                for source in self.config.get("sources", []):
                    if source.get("type") == "file":
                        df = plugin_module.execute(self.spark, source, self.config)
                        if df and not df.isEmpty():
                            collected_data.append({"name": source.get("name"), "df": df})
            
            if not collected_data:
                logger.warning("⚠️ 수집된 데이터가 없어 파이프라인을 종료합니다.")
                return

            logger.info(f"✅ 1단계 완료: 총 {len(collected_data)}개 소스 수집 성공!")

            # ---------------------------------------------------------
            # 2단계: Parser (Process) - 개별 정제 후 병합
            # ---------------------------------------------------------
            logger.info("▶️ [Step 2] Parser 기반 데이터 정제 시작")
            process_module = importlib.import_module("backend.plugins.process.normalizer")
            
            parsed_dfs = []
            for item in collected_data:
                # ⭐️ 모양이 다른 각 로그를 먼저 표준 포맷으로 깎아냅니다.
                parsed_df = process_module.execute(self.spark, item["df"], item["name"])
                if parsed_df and not parsed_df.isEmpty():
                    parsed_dfs.append(parsed_df)

            if not parsed_dfs:
                logger.warning("⚠️ 정제된 유효 데이터가 없습니다.")
                return

            # ⭐️ 이제 모든 로그가 5칸짜리 표준 폼으로 똑같아졌으므로 안전하게 하나로 합칩니다!
            main_df = functools.reduce(DataFrame.unionByName, parsed_dfs)
            
            logger.info("✅ 2단계 정제 및 병합 완료! (아래는 정제된 샘플 데이터입니다)")
            #main_df.show(10, truncate=False)

            # ---------------------------------------------------------
            # 3단계: 분석 (Rule-based Detect)
            # ---------------------------------------------------------
            logger.info("▶️ [Step 3] 룰 기반 위협 분석 시작")
            rule_module = importlib.import_module("backend.plugins.detect.rule_engine")
            
            # 탐지 모듈 실행 (위험 데이터만 리턴됨)
            anomaly_df = rule_module.execute(self.spark, main_df, self.config)
            
            if anomaly_df and not anomaly_df.isEmpty():
                logger.info(f"🎯 파이프라인 분석 결과: 총 {anomaly_df.count()}건의 위협이 탐지되었습니다.")
            else:
                logger.info("🕊️ 탐지된 위협이 없습니다. 시스템이 안전합니다.")

            # [향후 4단계: 적재(Output) 플러그인이 여기에 연결됩니다]

            
        except Exception as e:
            logger.error(f"❌ 파이프라인 실행 중 치명적 오류 발생: {e}")
        finally:
            self.spark.stop()

if __name__ == "__main__":
    pipeline = UEBAPipeline()
    pipeline.run_pipeline()