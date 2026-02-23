from pyspark.sql.functions import col, hour, dayofweek, when, to_timestamp
from core.utils import get_logger

logger = get_logger("Plugin-AbnormalTime")

def execute(df, config=None):
    try:
        logger.info("🕒 [Plugin] 심야/주말 비정상 접근 분석 중...")
        
        # ⭐️ 대소문자 구분 없이 timestamp나 ts가 포함된 모든 컬럼 검색
        potential_cols = [c for c in df.columns if "timestamp" in c.lower() or "ts" in c.lower()]
        target_ts_col = potential_cols[0] if potential_cols else None
        
        if not target_ts_col:
            logger.warning(f"⚠️ 시간 컬럼을 찾을 수 없습니다. (현재 필드: {df.columns})")
            return df

        # 시간 타입으로 변환 및 분석
        df = df.withColumn("_temp_ts", to_timestamp(col(target_ts_col)))
        df = df.withColumn("hour", hour(col("_temp_ts")))
        df = df.withColumn("day_of_week", dayofweek(col("_temp_ts")))
        
        # 주말(1,7) 또는 심야(0~6시) 스코어링
        df = df.withColumn(
            "risk_score_time",
            when((col("day_of_week").isin([1, 7])), 30.0)
            .when((col("hour") >= 0) & (col("hour") <= 6), 50.0)
            .otherwise(0.0)
        )
        
        df = df.withColumn("risk_score", col("risk_score") + col("risk_score_time"))
        df = df.withColumn(
            "alert_reason",
            when(col("risk_score_time") > 0, "Abnormal Time Access").otherwise(col("alert_reason"))
        )
        
        return df.drop("_temp_ts", "hour", "day_of_week", "risk_score_time")
    except Exception as e:
        logger.error(f"❌ 분석 실패: {e}")
        return df