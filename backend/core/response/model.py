from dataclasses import dataclass


@dataclass(frozen=True)
class ThreatContext:
    entity_id: str
    source: str
    risk_score: float
    reason: str


@dataclass(frozen=True)
class ResponseAction:
    action_type: str
    target: str
    dry_run: bool = True