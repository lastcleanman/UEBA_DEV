from fastapi import APIRouter

# 기존 detect.py 와 ml_detect.py 의 기능을 하나로 묶습니다.
router = APIRouter(tags=["Detection"])

@router.get("/rules")
async def get_detection_rules():
    """(기존 Basic) 기본 임계치 및 룰 기반 탐지 규칙 조회"""
    return {"status": "success", "data": ["BruteForce_Login", "TCP_SYN_Flood"]}

@router.get("/ml-models")
async def get_ml_models():
    """(기존 Standard) 머신러닝 기반 이상 행위 탐지 모델 조회"""
    return {"status": "success", "data": ["IsolationForest_Anomaly", "AutoEncoder_Behavior"]}

@router.post("/scan")
async def run_detection_scan(payload: dict):
    """실시간/배치 탐지 스캔 실행"""
    return {"status": "success", "message": "탐지 스캔이 시작되었습니다."}