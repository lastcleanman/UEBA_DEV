from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class CandidateRule:
    name: str
    impact_score: float
    description: str


class GREService:
    """GRE(Generative Rule Engineering) 후보 룰 생성 스캐폴딩."""

    def mine_candidates(self, source_signals: Iterable[str]) -> List[CandidateRule]:
        results: List[CandidateRule] = []
        for signal in source_signals:
            key = signal.strip().lower()
            if not key:
                continue
            results.append(
                CandidateRule(
                    name=f"gre_{key}",
                    impact_score=70.0,
                    description=f"'{signal}' 기반 자동 생성 시나리오 후보",
                )
            )
        return results