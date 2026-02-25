from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class FeatureContribution:
    feature: str
    contribution: float


def build_narrative(contributions: Iterable[FeatureContribution]) -> str:
    """XAI 자연어 설명 스캐폴딩.

    SHAP 연동 이전 단계에서 상위 기여 피처를 문장으로 합성한다.
    """
    sorted_items = sorted(contributions, key=lambda x: abs(x.contribution), reverse=True)
    top = sorted_items[:3]
    if not top:
        return "주요 기여 요인이 충분하지 않아 추가 데이터가 필요합니다."

    parts = [f"{item.feature}({item.contribution:+.1f})" for item in top]
    return "위협 점수는 " + ", ".join(parts) + " 요인의 복합 영향으로 상승했습니다."