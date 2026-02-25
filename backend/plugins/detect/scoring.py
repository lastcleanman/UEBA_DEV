from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class RiskWeights:
    statistical: float = 0.25
    timeseries: float = 0.20
    peer_group: float = 0.20
    rarity: float = 0.15
    sequence: float = 0.20


class RiskScoreAggregator:
    """백서의 Unified Risk Score(0~100) 선형 결합 모델 스캐폴딩.

    실제 학습/튜닝 모델 연결 전까지, 엔진별 정규화 점수를 안전하게 합산한다.
    """

    def __init__(self, weights: RiskWeights | None = None):
        self.weights = weights or RiskWeights()

    @staticmethod
    def _clamp(score: float) -> float:
        return max(0.0, min(100.0, score))

    def aggregate(self, normalized_scores: Dict[str, float], user_risk_factor: float = 0.0) -> float:
        weighted = (
            normalized_scores.get("statistical", 0.0) * self.weights.statistical
            + normalized_scores.get("timeseries", 0.0) * self.weights.timeseries
            + normalized_scores.get("peer_group", 0.0) * self.weights.peer_group
            + normalized_scores.get("rarity", 0.0) * self.weights.rarity
            + normalized_scores.get("sequence", 0.0) * self.weights.sequence
        )
        boosted = weighted * (1.0 + max(0.0, user_risk_factor))
        return self._clamp(boosted)