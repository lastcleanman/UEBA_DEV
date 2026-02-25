from fastapi import APIRouter
router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@router.get("/summary")
def get_summary():
    return {"data": {"total_threats": 0, "top_risky_users": []}}

@router.get("/ml-metrics")
def get_ml_metrics():
    return {"total_analyzed": 0, "high_risk_count": 0, "status": "대기 중", "detection_list": []}
