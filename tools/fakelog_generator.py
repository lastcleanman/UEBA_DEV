import sys
import os
import json
import random
import time
from datetime import datetime
from sqlalchemy import create_engine, text

# ⭐️ 새로운 독립 환경 경로 추가 (코어 로거 사용)
if "/UEBA_DEV" not in sys.path:
    sys.path.insert(0, "/UEBA_DEV")

from core.utils import get_logger

logger = get_logger("MultiLogGenerator")
LOG_DIR = "/UEBA_DEV/data/logs/"
CONFIG_FILE = "/UEBA_DEV/conf/ueba_settings.json"

USER_ROSTER = []

def load_users_from_db():
    logger.info("🔄 설정 파일에서 DB 정보를 읽어옵니다...")
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # ueba_mariaDB 설정 가져오기
        db_conf = next((s for s in config.get("sources", []) if s.get("name") == "ueba_mariaDB"), None)
        if not db_conf:
            logger.error("❌ 설정 파일에 'ueba_mariaDB' 정보가 없습니다.")
            return False

        # DB_URL 자동 조합
        db_url = f"mysql+pymysql://{db_conf['user']}:{db_conf['password']}@{db_conf['host']}:{db_conf['port']}/{db_conf['database']}"
        engine = create_engine(db_url, pool_pre_ping=True)
        
        logger.info(f"🔄 MariaDB({db_conf['host']})에서 사원 정보를 불러오는 중...")
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    e.employee_id AS emp_id,
                    e.name_kr AS user_name,
                    COALESCE(d.department_name, 'Unknown') AS dept_name
                FROM sj_ueba_employees e
                LEFT JOIN sj_ueba_departments d ON e.department_id = d.department_id
                WHERE e.employee_id IS NOT NULL AND e.name_kr IS NOT NULL
            """)
            result = conn.execute(query)
            
            for idx, row in enumerate(result):
                ip_subnet = (idx % 20) + 10
                ip_host = (idx % 250) + 1
                assigned_ip = f"192.168.{ip_subnet}.{ip_host}"
                
                USER_ROSTER.append({
                    "user_id": row.emp_id,       
                    "user": row.user_name,       
                    "dept": row.dept_name,       
                    "ip": assigned_ip,
                    "device_id": f"WS-{row.emp_id}"
                })
                
        logger.info(f"✅ 총 {len(USER_ROSTER)}명의 사원 정보를 성공적으로 로드했습니다!")
        return True
        
    except Exception as e:
        logger.error(f"❌ DB 연동 실패: {e}")
        return False

def write_log(filename, data):
    os.makedirs(LOG_DIR, exist_ok=True)
    filepath = os.path.join(LOG_DIR, filename)
    
    # ⭐️ 딕셔너리를 깨끗하게 JSON 한 줄로 저장
    with open(filepath, "a", encoding="utf-8") as f:
        json_line = json.dumps(data, ensure_ascii=False).strip()
        f.write(json_line + "\n")

def generate_logs(count=5):
    if not USER_ROSTER: return
        
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for _ in range(count):
        actor = random.choice(USER_ROSTER)
        
        base_info = {
            "timestamp": now_str,
            "user_id": actor["user_id"], 
            "user": actor["user"],       
            "department": actor["dept"]  
        }
        
        # 엔진이 수집할 수 있도록 파일명 규격(Auth_Logs.log 등)으로 맞춰서 저장합니다.
        # [1] 인증 로그
        auth_data = {**base_info, "action": random.choices(["login", "logout", "fail"], weights=[70, 20, 10])[0], "ip": actor["ip"]}
        write_log("Auth_Logs.log", auth_data)

        # [2] 웹 서버 로그
        web_data = {**base_info, "action": random.choices(["view", "download", "upload"], weights=[80, 15, 5])[0], "resource": random.choice(["/api/v1/data", "/hr/salary.pdf", "/sales/report.xlsx"]), "ip": actor["ip"]}
        write_log("Web_Logs.log", web_data)

        # [3] 엔드포인트 로그
        endpoint_data = {**base_info, "action": random.choices(["process_start", "file_copy", "USB_inserted"], weights=[80, 15, 5])[0], "device_id": actor["device_id"]}
        write_log("Endpoint_Logs.log", endpoint_data)

        # [4] 방화벽 정책 로그
        fw_data = {**base_info, "src_ip": actor["ip"], "dst_ip": f"10.0.{random.randint(1,5)}.{random.randint(1,255)}", "action": random.choices(["allow", "deny"], weights=[90, 10])[0], "port": random.choice([80, 443, 22])}
        write_log("Firewall_Logs.log", fw_data)

def main():
    logger.info("🚀 고급 JSON UEBA Fake Log 생성기 시작...")
    if load_users_from_db():
        try:
            while True:
                generate_logs(5)
                logger.info("-" * 70)
                time.sleep(5)
        except KeyboardInterrupt:
            logger.info("\n🛑 생성기를 종료합니다.")
    else:
        logger.error("⚠️ 사원 정보를 불러오지 못해 생성기를 종료합니다.")

if __name__ == "__main__":
    main()