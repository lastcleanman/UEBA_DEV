import pandas as pd
import datetime
import os

# 데이터가 저장될 경로 (현재 설정 파일의 소스 경로에 맞게 조정 필요)
# 보통 입력 플러그인이 읽어가는 기본 폴더를 가정합니다.
DUMMY_DIR = "/UEBA_DEV/backend/data/raw_logs"
os.makedirs(DUMMY_DIR, exist_ok=True)

now = datetime.datetime.now()

# 1. Auth_Logs 더미 데이터 (비정상 로그인 시나리오)
auth_data = [
    {"timestamp": str(now - datetime.timedelta(minutes=10)), "user_id": "admin", "event_type": "login_success", "ip": "192.168.1.10"},
    {"timestamp": str(now - datetime.timedelta(minutes=5)), "user_id": "hacker", "event_type": "login_failed", "ip": "203.0.113.50"},
    {"timestamp": str(now), "user_id": "hacker", "event_type": "login_success", "ip": "203.0.113.50"}
]
pd.DataFrame(auth_data).to_csv(f"{DUMMY_DIR}/Auth_Logs.csv", index=False)

print("✅ 더미 데이터가 성공적으로 생성되었습니다!")