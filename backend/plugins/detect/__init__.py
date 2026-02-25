"""Detection domain package.

백서 Ⅱ-4 다층 분석 엔진 구조 반영을 위한 도메인 루트.
"""

from .scoring import RiskScoreAggregator

__all__ = ["RiskScoreAggregator"]