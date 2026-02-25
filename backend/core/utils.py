import os
import logging
from backend.core.config import LOG_DIR

def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 콘솔 출력
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # ⭐️ 1. 로그를 저장할 올바른 경로 설정
        os.makedirs(LOG_DIR, exist_ok=True)
        fh = logging.FileHandler(os.path.join(LOG_DIR, 'ueba_engine.log'))
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger

def get_spark_session(app_name="UEBA_Enterprise_Engine"):
    """
    [유연성 강화 구조] Java 버전에 종속되지 않는 범용 PySpark 세션 생성기
    어떤 버전의 JVM이 설치되어 있더라도 PySpark 구동기 레벨에서 동적으로 보안 옵션을 주입합니다.
    """
    
    # 1. 범용 JVM 메모리 접근 허용 옵션 (어떤 버전이든 호환되도록 강제 주입)
    universal_jvm_opts = (
        "--add-opens=java.base/java.nio=ALL-UNNAMED "
        "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED "
        "--add-opens=java.base/java.lang.invoke=ALL-UNNAMED "
        "--add-opens=java.base/java.util=ALL-UNNAMED"
    )
    
    # 2. ⭐️ OS가 아닌 PySpark 코어 런타임에 직접 주입 (이 방식은 절대 무시되지 않습니다)
    os.environ["PYSPARK_SUBMIT_ARGS"] = f"--driver-java-options '{universal_jvm_opts}' pyspark-shell"
    
    from pyspark.sql import SparkSession

    # 3. Spark 빌더 설정 (Master 통신 및 Executor 옵션 동시 적용)
    spark = SparkSession.builder \
        .appName(app_name) \
        .master("spark://ueba-spark:7077") \
        .config("spark.driver.bindAddress", "0.0.0.0") \
        .config("spark.driver.host", "ueba-backend") \
        .config("spark.executor.memory", "1g") \
        .config("spark.executor.extraJavaOptions", universal_jvm_opts) \
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("ERROR")
    return spark