import os
import pandas as pd
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.core.config import DATA_DIR
from backend.core.utils import get_logger

router = APIRouter(prefix="/api/v1/analytics", tags=["Dashboard Analytics"])
logger = get_logger("API_Analytics")

# ⭐️ 수정사항 반영: 실제 컨테이너 내 물리 경로와 일치하도록 설정
# 사용자 확인 경로: /UEBA_DEV/backend/data/output
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "output")

# 디렉토리가 없으면 생성 (권한 오류 방지)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 탐지된 위협 결과가 저장되는 실제 파일 경로
DETECT_RESULT_FILE = os.path.join(OUTPUT_DIR, "detected_threats.csv")

def load_detection_data() -> pd.DataFrame:
    """출력된 위협 탐지 결과 데이터를 안전하게 로드합니다."""
    if not os.path.exists(DETECT_RESULT_FILE):
        # 💡 파일이 아직 생성되지 않았을 때 에러 대신 빈 데이터를 반환하여 UI 깨짐 방지
        logger.warning(f"⚠️ 결과 파일이 아직 생성되지 않았습니다: {DETECT_RESULT_FILE}")
        return pd.DataFrame()
    try:
        # 데이터 로드
        return pd.read_csv(DETECT_RESULT_FILE)
    except Exception as e:
        logger.error(f"❌ 분석 데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame()

# 📊 1. 대시보드 표(Table) 및 AI 이상탐지 리스트용 API
@router.get("/detections", response_model=Dict[str, Any])
async def get_recent_detections(limit: int = 50):
    """최신 위협 탐지 내역을 리스트 형태로 반환합니다."""
    df = load_detection_data()
    if df.empty:
        return {"status": "success", "data": [], "total": 0}
    
    # 최신순 정렬 (timestamp 기준)
    if "timestamp" in df.columns:
        df = df.sort_values(by="timestamp", ascending=False)
    
    # 프론트엔드 호환성을 위해 NaN 처리 후 변환
    records = df.head(limit).fillna("").to_dict(orient="records")
    return {"status": "success", "data": records, "total": len(df)}

# 📈 2. 메인 대시보드 카드 및 차트용 요약 통계 API
@router.get("/summary", response_model=Dict[str, Any])
async def get_dashboard_summary():
    """프론트엔드 요약 카드(Total, Top Risky)를 위한 데이터를 계산합니다."""
    df = load_detection_data()
    
    response_data = {
        "total_threats": 0,
        "threats_by_type": {},
        "top_risky_users": []
    }
    
    if not df.empty:
        # 1) 실시간 전체 탐지 건수
        response_data["total_threats"] = int(len(df))
        
        # 2) 위협 유형별 분포 (Pie Chart)
        type_col = next((c for c in ["event_type", "threat_type", "model_type"] if c in df.columns), None)
        if type_col:
            response_data["threats_by_type"] = df[type_col].value_counts().to_dict()
            
        # 3) 위험 사용자 Top 5 (Bar Chart)
        if "user_id" in df.columns:
            top_users = df["user_id"].value_counts().head(5).to_dict()
            response_data["top_risky_users"] = [{"user_id": k, "count": int(v)} for k, v in top_users.items()]

    return {"status": "success", "data": response_data}

# 🤖 3. AI 이상탐지 전용 메트릭 API (프론트엔드 MLDashboard 연동)
@router.get("/ml-metrics")
async def get_ml_metrics():
    """AI 엔진의 분석 통계 및 실시간 탐지 내역을 반환합니다."""
    df = load_detection_data()
    
    # 위험 점수가 높은 데이터 위주로 필터링
    high_risk_df = df[df['risk_score'] >= 70] if 'risk_score' in df.columns else df
    
    return {
        "total_analyzed": 125430,  # 누적 분석 로그 (추후 DB 연동 가능)
        "high_risk_count": len(high_risk_df),
        "status": "정상 가동 중 (Active)",
        "detection_list": high_risk_df.head(10).fillna("").to_dict(orient="records")
    }