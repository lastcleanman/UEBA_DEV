from pyspark.sql.functions import col, when, lit
from backend.core.utils import get_logger

logger = get_logger("Plugin-Detect")

def execute(spark, df, global_config):
    logger.info(f"🚨 [Step 3] 룰 기반 위협 탐지(Rule Engine) 시작 (분석 대상: {df.count()}건)")
    
    try:
        # 1. 위협 탐지 룰 적용: 웹 탐지(DETECT) 이벤트가 발생한 경우 위험도 80점 부여
        df_scored = df.withColumn(
            "risk_score",
            when(col("event_type") == "DETECT", lit(80)).otherwise(lit(0))
        ).withColumn(
            "threat_name",
            when(col("event_type") == "DETECT", lit("웹 공격 (WAF 차단/탐지)")).otherwise(lit("Normal"))
        )
        
        # 2. 위험 점수가 0점 초과인 '진짜 위협'만 걸러내기
        anomaly_df = df_scored.filter(col("risk_score") > 0)
        anomaly_count = anomaly_df.count()
        
        logger.info(f"✅ [Step 3] 위협 탐지 완료! (발견된 이상 행위: {anomaly_count}건)")
        
        if anomaly_count > 0:
            logger.info("🔥 [탐지된 위협 샘플]")
            anomaly_df.show(5, truncate=False)
            
        return anomaly_df

    except Exception as e:
        logger.error(f"❌ [Step 3] 탐지 엔진 오류: {e}")
        return df