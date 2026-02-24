import sys
import os
import json
import random
import time
from datetime import datetime
from sqlalchemy import create_engine, text

# 독립 환경 경로 추가
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
            
        db_conf = next((s for s in config.get("sources", []) if s.get("name") == "ueba_mariaDB"), None)
        if not db_conf:
            logger.error("❌ 설정 파일에 'ueba_mariaDB' 정보가 없습니다.")
            return False

        db_url = f"mysql+pymysql://{db_conf['user']}:{db_conf['password']}@{db_conf['host']}:{db_conf['port']}/{db_conf['database']}"
        engine = create_engine(db_url, pool_pre_ping=True)

        logger.info(f"🔄 MariaDB({db_conf['host']})에서 사원 정보를 불러오는 중...")
        with engine.connect() as conn:
            query = text("SELECT e.employee_id AS emp_id, e.name_kr AS user_name FROM sj_ueba_employees e WHERE e.employee_id IS NOT NULL")
            result = conn.execute(query)
            for row in result:
                USER_ROSTER.append({"user_id": row.emp_id, "user": row.user_name})
                
        logger.info(f"✅ 총 {len(USER_ROSTER)}명의 사원 정보를 로드했습니다!")
        return True
    except Exception as e:
        logger.error(f"❌ DB 연동 실패: {e}")
        return False

def write_waf_log(filename, log_line):
    os.makedirs(LOG_DIR, exist_ok=True)
    filepath = os.path.join(LOG_DIR, filename)
    # AIWAF 규격은 JSON이 아닌 평문(String) + 구분자(|) 형태입니다.
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")

def generate_logs(count=2):
    if not USER_ROSTER: return
    
    # [공통 필드] AIWAF v5.0.2 규격 (YYYY-MM-DD HH:MM:SS)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mgmt_ip = "10.0.2.115"
    version = "v5.0.2"
    sep = "|" # 항목 구분자

    for _ in range(count):
        actor = random.choice(USER_ROSTER)
        client_ip = f"192.168.10.{random.randint(1, 254)}"
        is_attack = random.random() < 0.1

        # -----------------------------------------------------------------
        # 1. 탐지 로그 (DETECT) -> 엔진의 Web_Logs와 매핑
        # -----------------------------------------------------------------
        # 규격: 로그유형|식별ID|시간|식별IP|버전|C_IP|C_PORT|S_IP|S_PORT|도메인|룰이름|위험도|조치|요청데이터|탐지코드|탐지유형|탐지근거|프로토콜|호스트|경로|요청길이|OriginIP|국가|국가(Origin)|사용자정의
        detect_fields = [
            "DETECT", "WAF", now_str, mgmt_ip, version,
            client_ip, str(random.randint(10000, 65535)), "10.0.2.245", "80", "monitorapp.com",
            "TEST SQL Injection" if is_attack else "XSS Attack",
            "높음" if is_attack else "중간",
            "차단" if is_attack else "탐지",
            "[Empty value]", "1", "SQL 인젝션", "[query/payload monitorapp]", "http", "monitorapp.com", "/?monitorapp=monitorapp",
            "1536", "없음", "[Empty value]", "[Empty value]",
            f"USER_ID={actor['user_id']} USER_NAME={actor['user']}" # 임의설정값에 사용자 정보 매핑
        ]
        write_waf_log("Web_Logs.log", sep.join(detect_fields))

        # -----------------------------------------------------------------
        # 2. 감사 로그 (AUDIT) -> 엔진의 Auth_Logs와 매핑
        # -----------------------------------------------------------------
        # 규격: 로그유형|식별ID|시간|식별IP|버전|C_IP|아이디|감사유형|감사데이터|사용자정의
        audit_fields = [
            "AUDIT", "WAF", now_str, mgmt_ip, version,
            client_ip, actor['user'],
            "정책 적용" if is_attack else "로그인",
            f"사용자 {actor['user']} 작업 수행",
            f"USER_ID={actor['user_id']}"
        ]
        write_waf_log("Auth_Logs.log", sep.join(audit_fields))

        # -----------------------------------------------------------------
        # 3. 트래픽 로그 (TRAFFIC) -> 엔진의 Firewall_Logs와 매핑
        # -----------------------------------------------------------------
        # 규격: 로그유형|식별ID|시간|식별IP|버전|도메인|BPS(전체)|BPS(HTTP)|...|사용자정의
        traffic_fields = [
            "TRAFFIC", "WAF", now_str, mgmt_ip, version,
            "Etc.", "10312694.4", "10312694.4", "[Empty value]", 
            "42.3", "42.3", "[Empty value]", "7.8", "[Empty value]", "7.8", 
            "19", "0", "19", "1", "0", "1", "0", "29",
            "TRAFFIC_STAT=OK"
        ]
        write_waf_log("Firewall_Logs.log", sep.join(traffic_fields))

        # -----------------------------------------------------------------
        # 4. 시스템 로그 (SYSTEM) -> 엔진의 Endpoint_Logs와 매핑
        # -----------------------------------------------------------------
        # 규격: 로그유형|식별ID|시간|식별IP|버전|GW개수|GW상태|링크상태|CPU|SelectCPU|평균CPU|온도|메모리|디스크|사용자정의
        system_fields = [
            "SYSTEM", "WAF", now_str, mgmt_ip, version,
            "6", "정상", "eth0(UP,1000,full)",
            str(random.randint(10, 50)), str(random.randint(10, 50)), str(random.randint(10, 50)),
            "40", str(random.randint(30, 70)), str(random.randint(20, 60)),
            "SYS_STAT=OK"
        ]
        write_waf_log("Endpoint_Logs.log", sep.join(system_fields))

    if is_attack:
        logger.warning(f"🔥 [Anomaly Alert] {actor['user']}에 의한 이상 징후(DETECT) 생성됨!")

def main():
    logger.info("🚀 AIWAF v5.0.2 규격 (구분자 포맷) 로그 생성기 시작...")
    if load_users_from_db():
        try:
            while True:
                generate_logs(2)
                logger.info("-" * 70)
                time.sleep(10) # AIWAF 권장 전송 주기 10초
        except KeyboardInterrupt:
            logger.info("\n🛑 생성기를 종료합니다.")
    else:
        logger.error("⚠️ 사원 정보를 불러오지 못해 생성기를 종료합니다.")

if __name__ == "__main__":
    main()