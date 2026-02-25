from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class JustificationRequest:
    case_id: str
    user_id: str
    reason_prompt: str


class JustificationService:
    """Human-in-the-Loop 소명 워크플로우 스캐폴딩."""

    def build_message(self, req: JustificationRequest) -> str:
        now = datetime.now(timezone.utc).isoformat()
        return (
            f"[UEBA 소명요청] case={req.case_id}, user={req.user_id}, "
            f"time={now}, reason={req.reason_prompt}"
        )