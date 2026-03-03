from collections import deque
from threading import Lock
from typing import Any, Deque, Dict, List, Tuple


class BufferManager:
    """
    - (tenant_id, source_id)별 버퍼
    - 전체 스트림용 global 버퍼
    - item dict 전체를 그대로 저장(추가 필드 포함)
    """

    def __init__(self, maxlen: int = 5000):
        self.maxlen = maxlen
        self._lock = Lock()

        self._per_source: Dict[Tuple[str, str], Deque[Dict[str, Any]]] = {}
        self._global: Deque[Dict[str, Any]] = deque(maxlen=maxlen)

    def push(self, tenant_id: str, source_id: str, item: Dict[str, Any]) -> None:
        # item dict 전체 보존 + tenant/source는 강제 주입
        event = dict(item or {})
        event["tenant_id"] = tenant_id
        event["source_id"] = source_id

        key = (tenant_id, source_id)
        with self._lock:
            if key not in self._per_source:
                self._per_source[key] = deque(maxlen=self.maxlen)
            self._per_source[key].append(event)
            self._global.append(event)

    def latest_global(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            buf = list(self._global)
        return buf[-limit:]

    def latest(self, tenant_id: str, source_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        key = (tenant_id, source_id)
        with self._lock:
            buf = list(self._per_source.get(key, deque()))
        return buf[-limit:]


# 싱글톤
global_buffer = BufferManager(maxlen=5000)