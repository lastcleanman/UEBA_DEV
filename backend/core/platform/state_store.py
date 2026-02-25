from abc import ABC, abstractmethod
from typing import Dict, Any


class PipelineStateStore(ABC):
    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def set_state(self, state: Dict[str, Any]) -> None:
        raise NotImplementedError


class InMemoryStateStore(PipelineStateStore):
    def __init__(self):
        self._state: Dict[str, Any] = {}

    def get_state(self) -> Dict[str, Any]:
        return dict(self._state)

    def set_state(self, state: Dict[str, Any]) -> None:
        self._state = dict(state)