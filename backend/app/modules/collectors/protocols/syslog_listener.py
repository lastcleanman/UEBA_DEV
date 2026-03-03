import socket
from datetime import datetime, timezone
from itertools import count
from typing import Any, Dict, List, Optional, Tuple

from app.core.ingestion.base_collector import BaseCollector
from app.core.logger import logger


class SyslogListenerCollector(BaseCollector):
    """
    UDP syslog listener
    - received_at / seq 를 이벤트에 추가
    - remote_addr도 함께 넣어 추적성 강화
    """

    def __init__(self, tenant_id: str, source_id: str, config: Dict[str, Any], buffer_manager):
        super().__init__(tenant_id, source_id, config, buffer_manager)
        self._sock: Optional[socket.socket] = None
        self._seq = count(1)

    async def on_start(self) -> None:
        host = self.config.get("host", "0.0.0.0")
        port = int(self.config.get("port", 5514))

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 수신 버퍼 조금 키우기(burst 대비)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024 * 1024)
        except Exception:
            pass

        sock.bind((host, port))
        sock.setblocking(False)

        self._sock = sock
        logger.info(f"✅ Syslog listener bound: {host}:{port} (udp)")

    async def on_stop(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        self._sock = None

    async def fetch_batch(self) -> List[Dict[str, Any]]:
        if not self._sock:
            return []

        events: List[Dict[str, Any]] = []

        for _ in range(self.batch_size):
            try:
                data, addr = self._sock.recvfrom(65535)
            except BlockingIOError:
                break
            except OSError:
                break

            raw = data.decode("utf-8", errors="replace").strip()
            received_at = datetime.now(timezone.utc).astimezone().isoformat()
            seq = next(self._seq)

            ev: Dict[str, Any] = {
                "raw_data": raw,
                "offset": 0,  # UDP는 file offset 개념이 없어서 0 유지
                "received_at": received_at,
                "seq": seq,
                "remote_addr": {"ip": addr[0], "port": addr[1]} if isinstance(addr, tuple) else None,
            }
            events.append(ev)

        return events