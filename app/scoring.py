"""Delay-risk formula. Kept in one place so the UI can show the same math."""


def delay_risk_minutes(failure_probability: float, typical_delay_minutes: float) -> float:
    """Expected delay minutes if this asset fails in service.

    delay_risk = failure_probability × typical_delay_minutes
    """
    probability = min(max(failure_probability, 0.0), 1.0)
    delay = max(typical_delay_minutes, 0.0)
    return round(probability * delay, 1)
