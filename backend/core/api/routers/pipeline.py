from fastapi import APIRouter
router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline"])

@router.get("/status")
def get_status():
    return {"status": "idle"}

@router.post("/run")
def run_pipeline():
    return {"message": "파이프라인 실행 신호 수신 (엔진 연결 대기 중)"}
