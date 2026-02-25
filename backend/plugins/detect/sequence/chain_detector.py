from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SequenceEvent:
    event_type: str
    ts_epoch: int


def detect_kill_chain_like_pattern(events: Iterable[SequenceEvent]) -> bool:
    """간단한 시퀀스 탐지 스캐폴딩.

    예: VPN_LOGIN -> SYSTEM_LOGIN -> BULK_TRANSFER 순서가 나타나면 True.
    """
    ordered = sorted(events, key=lambda e: e.ts_epoch)
    signature = ["VPN_LOGIN", "SYSTEM_LOGIN", "BULK_TRANSFER"]
    index = 0

    for event in ordered:
        if event.event_type == signature[index]:
            index += 1
            if index == len(signature):
                return True
    return False