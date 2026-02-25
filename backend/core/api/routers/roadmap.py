from fastapi import APIRouter

from backend.core.detection import RiskScoreAggregator
from backend.core.detection.sequence import SequenceEvent, detect_kill_chain_like_pattern
from backend.core.detection.xai import FeatureContribution, build_narrative
from backend.core.intelligence.gre import GREService

router = APIRouter(prefix="/api/v1/roadmap", tags=["Roadmap Refactor"])


@router.get("/capabilities")
def get_capabilities_sample():
    aggregator = RiskScoreAggregator()
    score = aggregator.aggregate(
        {
            "statistical": 80,
            "timeseries": 70,
            "peer_group": 60,
            "rarity": 50,
            "sequence": 75,
        },
        user_risk_factor=0.5,
    )

    chain_detected = detect_kill_chain_like_pattern(
        [
            SequenceEvent(event_type="VPN_LOGIN", ts_epoch=1),
            SequenceEvent(event_type="SYSTEM_LOGIN", ts_epoch=2),
            SequenceEvent(event_type="BULK_TRANSFER", ts_epoch=3),
        ]
    )

    xai_message = build_narrative(
        [
            FeatureContribution("late_night_access", 35.0),
            FeatureContribution("foreign_ip", 28.0),
            FeatureContribution("bulk_download", 20.0),
        ]
    )

    gre = GREService()
    candidates = [c.__dict__ for c in gre.mine_candidates(["vpn*dlp", "hr*iam"])]

    return {
        "unified_risk_score_sample": score,
        "sequence_detection_sample": chain_detected,
        "xai_narrative_sample": xai_message,
        "gre_candidates_sample": candidates,
    }