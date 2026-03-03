from typing import Any, Dict, List, Tuple

from app.core.logger import logger
from app.core.ingestion.buffer_manager import global_buffer
from app.modules.collectors.protocols.file_tailer import FileTailerCollector
from app.modules.collectors.protocols.syslog_listener import SyslogListenerCollector

class EdgeHub:
    def __init__(self):
        self._collectors: Dict[Tuple[str, str], Any] = {}

    def _register(self, collector) -> None:
        key = (collector.tenant_id, collector.source_id)
        self._collectors[key] = collector

    async def start_all(self) -> None:
        """
        여기서는 예시로 tenants/acme 기준 2개 collector를 기동.
        (추후 tenant config 로딩 방식으로 확장 가능)
        """
        tenant_id = "acme"

        collector_specs: List[Dict[str, Any]] = [
            {
                "source_id": "file_event",
                "klass": FileTailerCollector,
                "config": {
                    "file_path": "/app/tests/data/logs/event.log",
                    "read_from": "end",
                    "batch_size": 50,
                    "poll_interval": 1.0,
                },
            },
            {
                "source_id": "syslog_event",
                "klass": SyslogListenerCollector,
                "config": {
                    "host": "0.0.0.0",
                    "port": 5514,
                    "batch_size": 50,
                    "poll_interval": 0.2,  # UDP burst 대응으로 조금 더 촘촘히
                },
            },
        ]

        for spec in collector_specs:
            source_id = spec["source_id"]
            klass = spec["klass"]
            config = spec["config"]

            try:
                c = klass(tenant_id=tenant_id, source_id=source_id, config=config, buffer_manager=global_buffer)
                self._register(c)
                await c.start()
            except Exception as e:
                logger.exception(f"❌ Collector start failed: {tenant_id}/{source_id} err={e}")

        logger.info("✅ EdgeHub/Collectors 기동 완료")

    async def stop_all(self) -> None:
        for key, c in list(self._collectors.items()):
            try:
                await c.stop()
            except Exception as e:
                logger.warning(f"Collector stop failed: {key} err={e}")

    def status(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for (_t, _s), c in self._collectors.items():
            out.append(
                {
                    "tenant_id": c.tenant_id,
                    "source_id": c.source_id,
                    "running": c.running,
                    "healthy": c.healthy,
                    "last_error": c.last_error,
                    "config": c.config,
                }
            )
        return out


global_edge_hub = EdgeHub()