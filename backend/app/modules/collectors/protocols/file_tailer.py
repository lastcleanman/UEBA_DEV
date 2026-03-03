import os
from typing import Any, Dict, List, Optional

from app.core.ingestion.base_collector import BaseCollector
from app.core.logger import logger


class FileTailerCollector(BaseCollector):
    """
    파일 tailer:
    - read_from: "start" | "end"
    - offset: byte offset
    """

    def __init__(self, tenant_id: str, source_id: str, config: Dict[str, Any], buffer_manager):
        super().__init__(tenant_id, source_id, config, buffer_manager)
        self._fp: Optional[Any] = None
        self._offset: int = 0

    async def on_start(self) -> None:
        file_path = self.config.get("file_path")
        if not file_path:
            raise ValueError("file_path is required")

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 파일이 없으면 생성
        open(file_path, "a", encoding="utf-8").close()

        self._fp = open(file_path, "r", encoding="utf-8", errors="replace")
        read_from = self.config.get("read_from", "end")

        if read_from == "start":
            self._fp.seek(0, os.SEEK_SET)
            self._offset = 0
        else:
            self._fp.seek(0, os.SEEK_END)
            self._offset = self._fp.tell()

        logger.info(f"✅ FileTailer ready: path={file_path} offset={self._offset} read_from={read_from}")

    async def on_stop(self) -> None:
        if self._fp:
            try:
                self._fp.close()
            except Exception:
                pass
        self._fp = None

    async def fetch_batch(self) -> List[Dict[str, Any]]:
        if not self._fp:
            return []

        events: List[Dict[str, Any]] = []
        file_path = self.config.get("file_path")

        for _ in range(self.batch_size):
            line = self._fp.readline()
            if not line:
                break
            self._offset = self._fp.tell()
            events.append(
                {
                    "raw_data": line.rstrip("\n"),
                    "offset": self._offset,
                    "file_path": file_path,
                }
            )
        return events