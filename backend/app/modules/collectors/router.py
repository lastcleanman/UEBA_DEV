from fastapi import APIRouter, Query
from pydantic import BaseModel

# ⭐️ 경로 수정: core에서 엔진 인스턴스를 가져옵니다.
from app.core.ingestion.buffer_manager import global_buffer
from app.core.ingestion.edge_hub import global_edge_hub

router = APIRouter(tags=["Collectors"])

@router.get("/status")
async def collectors_status():
    return {"status": "success", "collectors": global_edge_hub.status()}

@router.get("/stream")
async def collectors_stream(limit: int = Query(50, ge=1, le=5000)):
    data = global_buffer.latest_global(limit=limit)
    return {"status": "success", "count": len(data), "data": data}

# ⭐️ 추가: Dashboard "Apply" 버튼 404 에러 해결 API!
class UpdateConfigReq(BaseModel):
    tenant_id: str
    source_id: str
    read_from: str

@router.post("/config/read_from")
async def update_read_from_config(req: UpdateConfigReq):
    try:
        key = (req.tenant_id, req.source_id)
        target_collector = global_edge_hub._collectors.get(key)

        if not target_collector:
            return {"status": "error", "message": "수집기를 찾을 수 없습니다."}
        
        # 1. 수집기 일시 정지
        await target_collector.stop()
        
        # 2. 설정 변경 (end or begin)
        target_collector.config["read_from"] = req.read_from
        
        # 3. 재시작
        await target_collector.start()
        
        return {"status": "success", "message": f"수집기가 '{req.read_from}' 모드로 재시작되었습니다."}
    except Exception as e:
        return {"status": "error", "message": f"설정 변경 실패: {str(e)}"}