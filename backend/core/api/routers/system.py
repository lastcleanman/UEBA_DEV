import os
import json
import datetime
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/system", tags=["System Management"])

# 프로젝트 최상단 경로 설정
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
LOG_DIR = os.path.join(BASE_DIR, "logs")
# 로그 폴더가 없으면 data/logs를 바라보도록 유연하게 설정
if not os.path.exists(LOG_DIR):
    LOG_DIR = os.path.join(BASE_DIR, "data", "logs")

CONF_DIR = os.path.join(BASE_DIR, "conf")
PARSERS_DIR = os.path.join(CONF_DIR, "parsers")
SETTINGS_FILE = os.path.join(CONF_DIR, "ueba_settings.json")

# 📊 1. 로그 파일 날짜 목록 조회 API
@router.get("/log-dates")
def get_log_dates():
    if not os.path.exists(LOG_DIR):
        return {"dates": []}
    
    files = []
    for f in os.listdir(LOG_DIR):
        if f.endswith(".log"):
            filepath = os.path.join(LOG_DIR, f)
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            mtime = os.path.getmtime(filepath)
            dt = datetime.datetime.fromtimestamp(mtime)
            
            # 오늘 수정된 파일은 'Today' 라벨 부여
            date_str = "Today" if dt.date() == datetime.date.today() else dt.strftime("%Y-%m-%d")
            files.append({
                "date": date_str,
                "file": f,
                "size": f"{size_mb:.2f} MB",
                "timestamp": mtime
            })
    
    # 최신 파일이 위로 오도록 정렬
    files.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"dates": files}

# 📜 2. 특정 로그 파일 텍스트 조회 API
@router.get("/logs")
def get_logs(file: str):
    # 경로 조작(Directory Traversal) 해킹 방지 방어코드
    if ".." in file or "/" in file:
        raise HTTPException(status_code=400, detail="잘못된 파일명입니다.")
        
    filepath = os.path.join(LOG_DIR, file)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="로그 파일이 존재하지 않습니다.")
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # 브라우저 메모리 폭주를 막기 위해 최신 1000줄만 반환
        return {"logs": [line.strip() for line in lines[-1000:]]}
    except Exception as e:
        return {"logs": [f"❌ 로그를 읽는 중 오류 발생: {str(e)}"]}

# 🧩 3. 파서 규칙(XML) 목록 조회 API
@router.get("/parsers")
def get_parsers():
    parsers = {}
    if os.path.exists(PARSERS_DIR):
        for f in os.listdir(PARSERS_DIR):
            if f.endswith(".xml"):
                with open(os.path.join(PARSERS_DIR, f), "r", encoding="utf-8") as xml_file:
                    parsers[f] = xml_file.read()
    return {"parsers": parsers}

# 🔑 4. 시스템 라이선스 설정 조회 API
@router.get("/license")
def get_license():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        system_conf = config.get("system", {})
        tier = system_conf.get("license_tier", "enterprise")
        
        # 파이프라인 블록에서 활성화된 플러그인 목록을 긁어옴
        plugins = []
        pipeline = config.get("pipeline", {})
        for stage in ["input", "process", "detection", "output"]:
            plugins.extend(pipeline.get(stage, []))
            
        return {"tier": tier, "plugins": plugins}
    except Exception as e:
        return {"tier": "enterprise", "plugins": []}