from fastapi import APIRouter, HTTPException
import json
import subprocess
from pydantic import BaseModel
from typing import List
from backend.core.config import CONFIG_FILE

router = APIRouter()

class LicenseUpdateRequest(BaseModel):
    tier: str
    plugins: List[str]

@router.get("/api/license")
def get_license():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f: config = json.load(f)
        tier = config.get("system", {}).get("license_tier", "basic")
        plugins = config.get("pipeline", {}).get("detection", [])
        return {"tier": tier, "plugins": plugins}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/license")
def update_license(data: LicenseUpdateRequest):
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f: 
            config = json.load(f)

        if "system" not in config: config["system"] = {}
        config["system"]["license_tier"] = data.tier

        if "pipeline" not in config: config["pipeline"] = {}
        config["pipeline"]["detection"] = data.plugins

        # 파일 저장 (이 순간 엔진이 다음 주기에 바뀐 파일을 읽어갑니다)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        # ⭐️ Docker 강제 재시작 코드 삭제 ⭐️
        
        return {
            "status": "success", 
            "message": f"{data.tier.upper()} 등급 적용 완료!\n(엔진이 30초 내에 변경된 라이선스 모듈을 자동 반영합니다.)"
        }
    except Exception as e: 
        raise HTTPException(status_code=500, detail=str(e))