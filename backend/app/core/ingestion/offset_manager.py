import os
import json
import asyncio
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("OffsetManager")

class LocalOffsetManager:
    """
    수집기가 어디까지 읽었는지(Offset)를 로컬 JSON 파일에 기록하고 불러오는 클래스입니다.
    """
    def __init__(self, storage_path: str = "/app/data/offsets.json"):
        self.storage_path = storage_path
        self.offsets: Dict[str, int] = {}
        self._load_offsets()

    def _load_offsets(self):
        """디스크에서 기존 오프셋 기록을 불러옵니다."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.offsets = json.load(f)
            except Exception as e:
                logger.error(f"오프셋 파일을 읽는 중 오류 발생: {e}")

    def _save_offsets(self):
        """현재 메모리의 오프셋 기록을 디스크에 안전하게 저장합니다."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        try:
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.offsets, f, indent=4)
        except Exception as e:
            logger.error(f"오프셋 저장 중 오류 발생: {e}")

    async def get_offset(self, tenant_id: str, source_id: str) -> Optional[int]:
        """특정 테넌트/소스의 마지막 읽기 위치를 반환합니다."""
        key = f"{tenant_id}::{source_id}"
        return self.offsets.get(key)

    async def commit(self, tenant_id: str, source_id: str, last_record: Dict[str, Any]):
        """
        수집기가 데이터를 버퍼에 밀어넣은 직후 호출하여,
        마지막 레코드의 오프셋 위치를 기록(Commit)합니다.
        """
        key = f"{tenant_id}::{source_id}"
        offset = last_record.get("offset")
        
        if offset is not None:
            self.offsets[key] = offset
            # 실제 운영 환경에서는 디스크 I/O 부하를 줄이기 위해
            # 매번 저장하지 않고 주기적으로(예: 5초마다) 저장하는 로직을 추가하기도 합니다.
            self._save_offsets()

# 전역에서 공유할 싱글톤 인스턴스 생성
global_offset_manager = LocalOffsetManager()