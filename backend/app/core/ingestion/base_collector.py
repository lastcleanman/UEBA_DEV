import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.core.logger import logger


class BaseCollector(ABC):
    """
    공통 Collector 베이스:
    - poll_interval마다 fetch_batch() 호출
    - 결과를 buffer_manager에 push()
    - 예외는 collector 단위로 격리(healthy/last_error 갱신)
    """

    def __init__(
        self,
        tenant_id: str,
        source_id: str,
        config: Dict[str, Any],
        buffer_manager,
    ):
        self.tenant_id = tenant_id
        self.source_id = source_id
        self.config = config or {}
        self.buffer_manager = buffer_manager

        self.running: bool = False
        self.healthy: bool = True
        self.last_error: Optional[str] = None

        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    @property
    def poll_interval(self) -> float:
        try:
            return float(self.config.get("poll_interval", 1.0))
        except Exception:
            return 1.0

    @property
    def batch_size(self) -> int:
        try:
            return int(self.config.get("batch_size", 50))
        except Exception:
            return 50

    async def start(self) -> None:
        if self.running:
            return
        self._stop_event.clear()
        self.running = True
        self._task = asyncio.create_task(self._run_loop(), name=f"collector:{self.source_id}")
        logger.info(f"✅ Collector started: tenant={self.tenant_id} source={self.source_id}")

    async def stop(self) -> None:
        if not self.running:
            return
        self._stop_event.set()
        if self._task:
            try:
                await self._task
            except Exception as e:
                logger.warning(f"Collector task stop wait failed: {self.source_id} err={e}")
        self.running = False
        await self.on_stop()
        logger.info(f"🛑 Collector stopped: tenant={self.tenant_id} source={self.source_id}")

    async def _run_loop(self) -> None:
        try:
            await self.on_start()
        except Exception as e:
            self.healthy = False
            self.last_error = f"on_start failed: {e}"
            logger.exception(f"❌ on_start failed: {self.source_id}")

        while not self._stop_event.is_set():
            try:
                batch = await self.fetch_batch()
                if batch:
                    for item in batch:
                        # item은 dict 전체를 그대로 버퍼에 보관 (추가필드 포함)
                        self.buffer_manager.push(self.tenant_id, self.source_id, item)
                self.healthy = True
                self.last_error = None
            except Exception as e:
                self.healthy = False
                self.last_error = str(e)
                logger.exception(f"❌ Collector loop error: source={self.source_id}")
                # 실패해도 서버 전체는 죽지 않게 살짝 쉬고 계속
                await asyncio.sleep(min(self.poll_interval, 1.0))

            await asyncio.sleep(self.poll_interval)

    async def on_start(self) -> None:
        """선택: 리소스 오픈 등"""
        return

    async def on_stop(self) -> None:
        """선택: 리소스 정리 등"""
        return

    @abstractmethod
    async def fetch_batch(self) -> List[Dict[str, Any]]:
        """수집 batch 반환"""
        raise NotImplementedError