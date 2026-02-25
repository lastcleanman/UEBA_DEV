class WatchlistService:
    """고위험군 가중치 계산 스캐폴딩."""

    def risk_factor(self, tag: str | None) -> float:
        table = {
            "normal": 0.0,
            "high_risk": 0.5,
            "critical": 1.0,
        }
        return table.get((tag or "normal").lower(), 0.0)