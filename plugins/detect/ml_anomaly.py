from pyspark.sql.functions import col, hour, when, count, lit, to_timestamp
from pyspark.sql.window import Window
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.clustering import KMeans
from core.utils import get_logger

logger = get_logger("Plugin-MLAnomaly")

def execute(spark, df, source_name, config):
    try:
        logger.info("🤖 [Plugin] 머신러닝(ML) 기반 이상 행위 분석 시작...")
        
        total_count = df.count()
        if total_count < 2:  # K-Means(K=2)는 최소 2건 이상의 데이터가 필요함
            logger.info("⏩ 데이터 건수가 부족하여 ML 분석을 스킵합니다.")
            return df

        # 1. 시간 컬럼 확보
        ts_cols = [c for c in df.columns if "timestamp" in c.lower() or "ts" in c.lower()]
        if not ts_cols:
            return df
            
        # 2. 특징(Feature) 추출 및 결측치(Null) 완벽 방어 ⭐️
        df = df.withColumn("_ml_ts", to_timestamp(col(ts_cols[0])))
        df = df.withColumn("_hour", hour(col("_ml_ts")))
        df = df.fillna(0, subset=["_hour"])  # 시간 파싱 실패 시 0시(자정)로 기본값 처리
        
        # 문자로 된 action을 숫자로 변환
        if "action" in df.columns:
            indexer = StringIndexer(inputCol="action", outputCol="_action_idx", handleInvalid="keep")
            df = indexer.fit(df).transform(df)
        else:
            df = df.withColumn("_action_idx", lit(0.0))

        # 시간대와 행동을 벡터로 결합 (handleInvalid="keep"으로 에러 방지 ⭐️)
        assembler = VectorAssembler(inputCols=["_hour", "_action_idx"], outputCol="_features", handleInvalid="keep")
        ml_df = assembler.transform(df)

        # 3. 비지도 학습 (K-Means Clustering)
        kmeans = KMeans(k=2, seed=42, featuresCol="_features", predictionCol="_cluster")
        model = kmeans.fit(ml_df)
        pred_df = model.transform(ml_df)

        # 4. 이상 탐지 (전체 데이터의 20% 미만인 소수 군집을 이상행위로 간주)
        win = Window.partitionBy("_cluster")
        pred_df = pred_df.withColumn("_cluster_size", count("*").over(win))
        
        threshold = max(total_count * 0.2, 1)

        pred_df = pred_df.withColumn(
            "risk_score_ml",
            when(col("_cluster_size") < threshold, 40.0).otherwise(0.0)
        )

        # 5. 최종 위협 점수 합산
        pred_df = pred_df.withColumn("risk_score", col("risk_score") + col("risk_score_ml"))
        pred_df = pred_df.withColumn(
            "alert_reason",
            when(col("risk_score_ml") > 0, 
                 when(col("alert_reason") == "", "ML Anomaly (Rare Behavior)")
                 .otherwise(col("alert_reason"))
            ).otherwise(col("alert_reason"))
        )

        # 6. 임시 컬럼 깔끔하게 정리
        final_df = pred_df.drop("_ml_ts", "_hour", "_action_idx", "_features", "_cluster", "_cluster_size", "risk_score_ml")
        
        logger.info("✅ [Plugin] 머신러닝 이상 행위 분석 완료 및 위협 점수 부여 성공")
        return final_df

    except Exception as e:
        logger.error(f"❌ [Plugin] ML 분석 중 에러: {e}")
        return df