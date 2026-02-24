from pyspark.sql.functions import col, when, lit
from core.utils import get_logger

logger = get_logger("Plugin-RuleEngine")

def execute(spark, df, source_name, config):
    try:
        logger.info("🕵️ [Plugin] 룰 기반 위협 분석(Rule Engine) 시작...")
        
        # 기본 컬럼이 없다면 생성
        if "risk_score" not in df.columns:
            df = df.withColumn("risk_score", lit(0.0))
        if "alert_reason" not in df.columns:
            df = df.withColumn("alert_reason", lit(""))

        # ---------------------------------------------------------
        # [탐지 룰셋 1] 로그인 실패(LOGIN_FAILED) 탐지
        # ---------------------------------------------------------
        if "action" in df.columns:
            df = df.withColumn(
                "risk_score",
                when(col("action").rlike("(?i)fail|error|deny|block"), col("risk_score") + 30.0)
                .otherwise(col("risk_score"))
            )
            df = df.withColumn(
                "alert_reason",
                when(col("action").rlike("(?i)fail|error|deny|block"), 
                     when(col("alert_reason") == "", "Login/Access Failed")
                     .otherwise(col("alert_reason"))
                ).otherwise(col("alert_reason"))
            )
            
        logger.info("✅ [Plugin] 위협 분석 및 스코어링 완료")
        return df

    except Exception as e:
        logger.error(f"❌ [Plugin] Rule Engine 실행 중 에러: {e}")
        return df # 에러가 나도 파이프라인이 끊기지 않도록 원본 반환