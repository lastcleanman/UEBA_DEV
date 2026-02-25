from typing import Dict, Any
import requests

from backend.core.utils import get_logger

logger = get_logger("ResponseWebhook")


def send_webhook(url: str, payload: Dict[str, Any], timeout_sec: int = 5) -> bool:
    """SOAR/Webhook 연동 스캐폴딩.

    네트워크 오류를 삼키지 않고 False 반환 + 로깅한다.
    """
    try:
        resp = requests.post(url, json=payload, timeout=timeout_sec)
        if 200 <= resp.status_code < 300:
            return True
        logger.warning(f"Webhook non-2xx response: {resp.status_code} - {resp.text}")
        return False
    except Exception as exc:
        logger.error(f"Webhook send failed: {exc}")
        return False