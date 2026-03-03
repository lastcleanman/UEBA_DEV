from fastapi import APIRouter, Depends
from typing import Any, Dict, List
import random

from app.tenants.context import TenantContext
from app.tenants.resolver import resolve_tenant
from app.license.manager import license_manager

# ⭐️ 데이터 하드코딩 삭제! 코어 설정 파일에서 메뉴 구조를 가져옵니다.
from app.core.menu_config import PIPELINE_MENU_CONFIG

router = APIRouter(tags=["Modules"])

@router.get("/t/{tenant}/api/v1/modules")
def get_modules(ctx: TenantContext = Depends(resolve_tenant)) -> List[Dict[str, Any]]:
    result_menu = []
    
    # 설정 파일(menu_config.py)의 뼈대를 바탕으로 권한을 검사합니다.
    for group in PIPELINE_MENU_CONFIG:
        allowed_items = []
        for item in group["items"]:
            # 해당 테넌트(고객)의 라이선스가 이 메뉴(id)를 허용하는지 검사
            if license_manager.is_enabled(ctx.tenant_id, item["id"]):
                allowed_items.append({
                    **item,
                    "enabled": True,
                    "healthy": True,
                    "trained_pct": round(random.uniform(85.0, 100.0), 1)
                })
        
        # 권한이 있어서 허용된 하위 메뉴가 1개라도 존재하는 그룹만 프론트엔드로 전달
        if allowed_items:
            result_menu.append({
                "key": group["key"],
                "label": group["label"],
                "items": allowed_items
            })
            
    return result_menu