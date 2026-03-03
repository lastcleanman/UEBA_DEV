import json
from pathlib import Path
from typing import Any, Dict, Optional

from app.tenants.context import TenantContext

def _metric_path(ctx: TenantContext, module_id: str) -> Path:
    safe = module_id.replace("/", "_")
    return ctx.metrics_dir / f"{safe}.json"

def read_training_metric(ctx: TenantContext, module_id: str) -> Dict[str, Any]:
    p = _metric_path(ctx, module_id)
    if not p.exists():
        return {
            "trained_pct": 0.0,
            "data_points": 0,
            "last_trained_at": None,
            "last_error": None,
        }
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {
            "trained_pct": 0.0,
            "data_points": 0,
            "last_trained_at": None,
            "last_error": f"metric read error: {e}",
        }