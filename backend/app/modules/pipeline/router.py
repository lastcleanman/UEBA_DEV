from fastapi import APIRouter

router = APIRouter(tags=["Pipeline"])

@router.get("/jobs")
async def get_pipeline_jobs():
    """(기존 Enterprise) 대용량 Grep 파이프라인 및 분산 처리 작업 조회"""
    return {"status": "success", "jobs": []}

@router.post("/deploy")
async def deploy_pipeline(payload: dict):
    """신규 파이프라인 배포"""
    return {"status": "success", "message": "파이프라인 배포 성공"}