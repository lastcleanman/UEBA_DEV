import logging
import os
from pyspark.sql import SparkSession
from logging.handlers import TimedRotatingFileHandler

def get_logger(name, base_dir="/UEBA_DEV"):
    logger = logging.getLogger(name)
    
    # 로거에 핸들러가 없을 때만 초기화 (중복 출력 방지)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        log_dir = os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # 1. 콘솔 출력 핸들러 (docker logs -f 에서 보는 용도)
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # 2. ⭐️ 날짜별 파일 분리 핸들러 (Daily Rotating)
        log_file = os.path.join(log_dir, 'ueba_engine.log')
        
        # when="midnight": 매일 자정에 파일 분리
        # interval=1: 1일 단위
        # backupCount=30: 최대 30일치(한 달) 로그만 보관하고 가장 오래된 것은 자동 삭제
        fh = TimedRotatingFileHandler(
            filename=log_file,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8"
        )
        
        # 분리된 과거 로그 파일의 이름 형식 지정 (예: ueba_engine.log.2026-02-23)
        fh.suffix = "%Y-%m-%d"
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

def get_spark_session(app_name="UEBA_Enterprise_Engine"):
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.driver.memory", "4g") \
        .config("spark.sql.execution.arrow.pyspark.enabled", "false") \
        .getOrCreate()