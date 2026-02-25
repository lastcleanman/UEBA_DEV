import math


def z_score(value: float, mean: float, std_dev: float) -> float:
    """Z-Score 계산.

    std_dev가 0이면 분모 오류를 피하기 위해 0.0 반환.
    """
    if std_dev == 0:
        return 0.0
    return (value - mean) / std_dev


def normalize_z_to_risk(z: float, threshold: float = 3.0) -> float:
    """절대 z값을 0~100 위험 점수로 단순 정규화.

    threshold 이상이면 고위험(100)으로 포화.
    """
    ratio = min(1.0, abs(z) / max(threshold, 0.1))
    return math.floor(ratio * 100)