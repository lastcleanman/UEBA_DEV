from __future__ import annotations
from pathlib import Path
from fastapi import Depends, HTTPException, Path as PathParam

from app.tenants.context import TenantContext
from app.license.manager import license_manager

TENANTS_ROOT = Path("/UEBA/tenants")

def resolve_tenant(
    tenant: str = PathParam(..., min_length=2, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$"),
) -> TenantContext:
    # 1) license.yaml에 tenant가 존재해야 함
    try:
        _ = license_manager.get_tenant_license(tenant)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown tenant: {tenant}")

    # 2) 테넌트 디렉토리 존재/생성
    root = TENANTS_ROOT / tenant
    if not root.exists():
        # 운영에서는 자동 생성 대신 404로 막아도 됨
        root.mkdir(parents=True, exist_ok=True)
        (root / "config").mkdir(parents=True, exist_ok=True)
        (root / "data/raw").mkdir(parents=True, exist_ok=True)
        (root / "data/processed").mkdir(parents=True, exist_ok=True)
        (root / "models").mkdir(parents=True, exist_ok=True)
        (root / "artifacts/parsers").mkdir(parents=True, exist_ok=True)
        (root / "metrics").mkdir(parents=True, exist_ok=True)

    return TenantContext(tenant_id=tenant, root=root)