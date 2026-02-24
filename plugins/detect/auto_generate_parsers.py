import os
import json
import glob
import xml.etree.ElementTree as ET
from xml.dom import minidom
from sqlalchemy import create_engine, text
from core.utils import get_logger

logger = get_logger("AutoParserAI")
LOG_DIR = "/UEBA_DEV/data/logs"
PARSER_DIR = "/UEBA_DEV/conf/parsers"
CONFIG_FILE = "/UEBA_DEV/conf/ueba_settings.json"

# AIWAF v5.0.2 규격 표준 컬럼
AIWAF_SCHEMAS = {
    "DETECT": ["log_type", "device_id", "@timestamp", "mgmt_ip", "version", "src_ip", "src_port", "dst_ip", "dst_port", "domain", "rule_name", "severity", "action", "request_data", "detect_code", "detect_type", "detect_reason", "protocol", "host", "resource", "request_length", "origin_ip", "country", "country_origin", "user_defined"],
    "AUDIT": ["log_type", "device_id", "@timestamp", "mgmt_ip", "version", "src_ip", "user", "audit_type", "audit_data", "user_defined"],
    "TRAFFIC": ["log_type", "device_id", "@timestamp", "mgmt_ip", "version", "domain", "bps_total", "bps_http", "bps_https", "tps_total", "tps_http", "tps_https", "cps_http", "cps_https", "cps_total", "open_conn_http", "open_conn_https", "open_conn_total", "visitors", "visitors_origin", "attackers", "attackers_origin", "attack_count", "user_defined"],
    "SYSTEM": ["log_type", "device_id", "@timestamp", "mgmt_ip", "version", "gw_count", "gw_status", "link_status", "cpu", "select_cpu", "avg_cpu", "temp", "mem", "disk", "user_defined"]
}

def get_db_engine():
    """ueba_settings.json에서 MariaDB 접속 정보를 읽어 엔진을 반환합니다."""
    try:
        if not os.path.exists(CONFIG_FILE): return None
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        db_conf = next((s for s in config.get("sources", []) if s.get("name") == "ueba_mariaDB"), None)
        if not db_conf: return None
        
        url = f"mysql+pymysql://{db_conf['user']}:{db_conf['password']}@{db_conf['host']}:{db_conf['port']}/{db_conf['database']}"
        return create_engine(url, pool_pre_ping=True)
    except Exception as e:
        logger.error(f"❌ DB 연동 설정 읽기 실패: {e}")
        return None

def get_last_line(filepath):
    """파일의 가장 마지막 줄(최신 로그)을 효율적으로 읽어옵니다."""
    with open(filepath, 'rb') as f:
        try:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)
        return f.readline().decode('utf-8').strip()

def learn_and_update_schema(log_file):
    base_name = os.path.basename(log_file).split('.')[0]
    xml_path = os.path.join(PARSER_DIR, f"{base_name}.xml")
    
    last_line = get_last_line(log_file)
    if not last_line: return

    # 1. 최신 로그로부터 '새로운 스키마' 추출
    new_format = "json"
    new_delimiter = ","
    new_fields = []

    if last_line.startswith("{") and last_line.endswith("}"):
        try:
            data = json.loads(last_line)
            new_format = "json"
            new_fields = list(data.keys())
        except json.JSONDecodeError: pass
    else:
        delimiters = ['|', ',', '^', '\t']
        delimiter = max(delimiters, key=lambda d: last_line.count(d))
        if last_line.count(delimiter) > 0:
            new_format = "delimited"
            new_delimiter = delimiter
            splits = last_line.split(delimiter)
            log_type_marker = splits[0]
            
            for i in range(len(splits)):
                if log_type_marker in AIWAF_SCHEMAS and i < len(AIWAF_SCHEMAS[log_type_marker]):
                    new_fields.append(AIWAF_SCHEMAS[log_type_marker][i])
                else:
                    new_fields.append(f"col_{i}")

    if not new_fields: return

    # 2. 기존 XML 파서 스키마 읽기
    existing_fields = []
    existing_format = ""
    if os.path.exists(xml_path):
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            existing_format = root.get("format", "")
            existing_fields = [f.get("target") for f in root.findall(".//field")]
        except Exception: pass

    # 3. 스키마가 변경되었거나 파일이 없으면 재생성 및 DB 동기화
    if new_format != existing_format or new_fields != existing_fields:
        logger.info(f"🔄 [{base_name}] 데이터 스키마 변경 감지됨. 파서를 재생성합니다.")
        
        if os.path.exists(xml_path):
            os.remove(xml_path)
            
        parser_elem = ET.Element("parser", format=new_format)
        if new_format == "delimited":
            parser_elem.set("delimiter", new_delimiter)
            
        fields_elem = ET.SubElement(parser_elem, "fields")
        for i, field_name in enumerate(new_fields):
            if new_format == "delimited":
                ET.SubElement(fields_elem, "field", index=str(i), target=field_name)
            else:
                ET.SubElement(fields_elem, "field", source=field_name, target=field_name)

        os.makedirs(PARSER_DIR, exist_ok=True)
        xml_str = minidom.parseString(ET.tostring(parser_elem)).toprettyxml(indent="    ")
        xml_str = os.linesep.join([s for s in xml_str.splitlines() if s.strip()]) 
        
        # 물리 파일 저장
        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml_str)
            
        logger.info(f"✅ [{base_name}] 파서 재생성 완료 (필드 {len(new_fields)}개 장착)")

        # ⭐️ 4. MariaDB (sj_ueba_parsers) 동기화 로직
        db_engine = get_db_engine()
        if db_engine:
            try:
                with db_engine.begin() as conn:
                    # UPSERT 문법 (MariaDB)
                    conn.execute(text("""
                        INSERT INTO sj_ueba_parsers (source_name, parser_xml, created_at, updated_at)
                        VALUES (:name, :xml, NOW(), NOW())
                        ON DUPLICATE KEY UPDATE
                        parser_xml = :xml,
                        updated_at = NOW()
                    """), {"name": base_name, "xml": xml_str})
                logger.info(f"💾 [{base_name}] DB (sj_ueba_parsers) 동기화 완료! 프론트엔드 반영 대기.")
            except Exception as e:
                logger.error(f"❌ DB 동기화 실패: {e}")

def run_learning_parser():
    log_files = glob.glob(os.path.join(LOG_DIR, "*.log")) + glob.glob(os.path.join(LOG_DIR, "*.json"))
    for log_file in log_files:
        learn_and_update_schema(log_file)

if __name__ == "__main__":
    run_learning_parser()