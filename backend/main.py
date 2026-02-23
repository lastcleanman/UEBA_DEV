from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import os
import threading

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

LOG_FILE = "/UEBA_DEV/logs/ueba_engine.log"
DATA_DIR = "/UEBA_DEV/data"
MODE_FILE = os.path.join(DATA_DIR, "mode.txt")

# 초기 기동 시 모드 파일이 없으면 생성
if not os.path.exists(MODE_FILE):
    with open(MODE_FILE, "w") as f: f.write("manual")

@app.get("/api/logs")
def get_logs(lines: int = 200):
    if not os.path.exists(LOG_FILE):
        return {"logs": ["⏳ 로그 대기 중..."]}
    try:
        result = subprocess.run(['tail', '-n', str(lines), LOG_FILE], capture_output=True, text=True)
        return {"logs": result.stdout.split('\n')}
    except Exception as e: return {"logs": [f"❌ 로그 읽기 실패: {e}"]}

# ⭐️ 모드 조회 API
@app.get("/api/mode")
def get_mode():
    try:
        with open(MODE_FILE, "r") as f: return {"mode": f.read().strip()}
    except: return {"mode": "manual"}

# ⭐️ 모드 변경 API
@app.post("/api/mode/{new_mode}")
def set_mode(new_mode: str):
    if new_mode not in ["daemon", "manual"]:
        return {"status": "error", "message": "잘못된 모드입니다."}
    try:
        with open(MODE_FILE, "w") as f: f.write(new_mode)
        return {"status": "success", "message": f"✅ {new_mode.upper()} 모드로 변경되었습니다."}
    except Exception as e: return {"status": "error", "message": str(e)}

def trigger_task(stage_id):
    try:
        if stage_id in ["all", "input"]:
            subprocess.run(["python3", "/UEBA_DEV/tools/generate_multi_logs.py"])
        flag_path = os.path.join(DATA_DIR, f"trigger_{stage_id}.flag")
        open(flag_path, 'w').close()
    except Exception as e: print(e)

@app.post("/api/trigger/{stage_id}")
def trigger_pipeline(stage_id: str):
    threading.Thread(target=trigger_task, args=(stage_id,)).start()
    return {"status": "success", "message": f"✅ [{stage_id.upper()}] 수동 실행 신호 전송 완료!"}