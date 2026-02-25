import os
import xml.etree.ElementTree as ET
from pyspark.sql.functions import col, lit, expr
from backend.core.utils import get_logger

logger = get_logger("Plugin-Process")

def execute(spark, df, source_name, global_config):
    base_dir = global_config.get("system", {}).get("base_dir", "/UEBA_DEV")
    xml_path = os.path.join(base_dir, "conf", "parsers", f"{source_name}.xml")
    
    if os.path.exists(xml_path):
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            fmt = root.get("format", "json")
            
            # JSON일 때는 기존 방식(source -> target) 매핑
            if fmt == "json":
                # ⭐️ 핵심 수정: 'field' -> './/field' 로 변경
                for field in root.findall('.//field'):
                    src = field.get('source')
                    tgt = field.get('target')
                    if src and tgt and src in df.columns:
                        df = df.withColumn(tgt, col(src))
                        
            # Delimited일 때는 사용자 정의 필드 파싱 (AIWAF 최적화)
            elif fmt == "delimited":
                if "user_defined" in df.columns:
                    # USER_ID=123 같은 문자열에서 정규식으로 값만 추출
                    df = df.withColumn("user_id", expr("regexp_extract(user_defined, 'USER_ID=([^ ]+)', 1)"))
                    df = df.withColumn("user", expr("regexp_extract(user_defined, 'USER_NAME=([^ ]+)', 1)"))
                    
        except Exception as e: 
            logger.error(f"❌ [{source_name}] 파싱/정제 에러: {e}")

    # 필수 컬럼 보정 (분석 엔진이 터지지 않도록)
    for c, v in [("risk_score", 0.0), ("alert_reason", ""), ("log_source", source_name)]:
        if c not in df.columns: 
            df = df.withColumn(c, lit(v))
            
    # 빈 값(Empty value)을 Null로 치환하여 분석 정확도 향상
    for column in df.columns:
        df = df.withColumn(column, expr(f"nullif(`{column}`, '[Empty value]')"))
        
    return df