from fastapi import APIRouter

router = APIRouter(tags=["Scoring"])

@router.get("/risk-scores")
async def get_risk_scores(tenant_id: str):
    """(기존 Basic) 자산 및 사용자별 위험도 점수(Risk Score) 조회"""
    return {"status": "success", "tenant": tenant_id, "scores": []}

@router.post("/calculate")
async def calculate_score(payload: dict):
    """위험 점수 재계산"""
    return {"status": "success", "message": "점수 계산 완료"}