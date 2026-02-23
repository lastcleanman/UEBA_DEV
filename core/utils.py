import logging
import os
from pyspark.sql import SparkSession

def get_logger(name, base_dir="/UEBA_DEV"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        log_dir = os.path.join(base_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        fh = logging.FileHandler(os.path.join(log_dir, 'ueba_engine.log'))
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

def get_spark_session(app_name="UEBA_Enterprise_Engine"):
    return SparkSession.builder \
        .appName(app_name) \
        .config("spark.driver.memory", "4g") \
        .config("spark.sql.execution.arrow.pyspark.enabled", "false") \
        .getOrCreate()