import os
import xml.etree.ElementTree as ET
from pyspark.sql.functions import col, lit
from core.utils import get_logger

logger = get_logger("Plugin-Process")

def execute(spark, df, source_name, global_config):
    base_dir = global_config.get("system", {}).get("base_dir", "/UEBA_DEV")
    xml_path = os.path.join(base_dir, "conf", "parsers", f"{source_name}.xml")
    
    if not os.path.exists(xml_path):
        logger.warning(f"⚠️ 파서 없음: {source_name}.xml")
    else:
        try:
            tree = ET.parse(xml_path)
            for field in tree.getroot().findall('field'):
                if field.get('source') in df.columns:
                    df = df.withColumn(field.get('target'), col(field.get('source')))
        except Exception as e: logger.error(f"❌ 파싱 에러: {e}")

    for c, v in [("risk_score", 0.0), ("alert_reason", ""), ("log_source", source_name)]:
        if c not in df.columns: df = df.withColumn(c, lit(v))
        
    return df