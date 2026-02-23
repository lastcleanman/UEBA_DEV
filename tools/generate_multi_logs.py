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
    now_str = datetime.now().isoformat()
    
    # ⭐️ [고도화] 특정 사용자 1명을 '공격자'로 임시 지정 (학습용 이상치 생성)
    attacker = random.choice(USER_ROSTER)

    for i in range(count):
        # 10% 확률로 공격 시나리오 로그 생성
        is_attack = random.random() < 0.1 
        actor = attacker if is_attack else random.choice(USER_ROSTER)
        
        base_info = {
            "@timestamp": now_str,
            "user_id": actor["user_id"], 
            "user": actor["user"],       
            "department": actor["dept"]  
        }

        # [1] 인증 로그: Brute Force 공격 (짧은 시간 대량 실패)
        if is_attack:
            for _ in range(5): # 한 번에 5번의 실패 로그를 쏟아냄
                auth_data = {**base_info, "action": "fail", "ip": "10.99.99.99", "reason": "Invalid Password"}
                write_log("Auth_Logs.log", auth_data)
        else:
            auth_data = {**base_info, "action": random.choice(["login", "logout"]), "ip": actor["ip"]}
            write_log("Auth_Logs.log", auth_data)

        # [2] 웹 서버 로그: 대량 데이터 유출 (비정상 리소스 접근)
        web_action = "sensitive_export" if is_attack else "view"
        web_res = "/admin/db_backup.sql" if is_attack else "/main/index.html"
        web_data = {**base_info, "action": web_action, "resource": web_res, "ip": actor["ip"]}
        write_log("Web_Logs.log", web_data)

    if is_attack:
        logger.warning(f"🔥 [Anomaly Alert] {attacker['user']}에 의한 인위적 이상 징후 생성됨!")

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