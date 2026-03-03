from fastapi import APIRouter

router = APIRouter(tags=["SOAR"])

@router.get("/workflows")
async def get_workflows():
    """(기존 Basic) 기본 대응 워크플로우 조회"""
    return {"status": "success", "data": ["Block_IP", "Isolate_Host"]}

@router.get("/playbooks")
async def get_playbooks():
    """(기존 Standard/Enterprise) 고급 플레이북 및 서드파티 연동 API 조회"""
    return {"status": "success", "data": ["PaloAlto_Block_Rule", "Slack_Alert_Bot"]}

@router.post("/execute")
async def execute_playbook(playbook_id: str):
    """특정 플레이북(대응 룰) 수동 실행"""
    return {"status": "success", "message": f"Playbook {playbook_id} 실행 완료"}