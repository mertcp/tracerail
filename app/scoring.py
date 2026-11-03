"""TraceRail turns measurements into health and delay risk.

The train sends currents, times, pressures, and temperatures.
It does not send a health status or a maintenance instruction.
The limits below are demo limits for Nordic Metro, not a manufacturer's specification.
"""

# Each signal is metric, normal value, limit, True when a higher reading is worse.
SIGNALS = {
    "doors": (
        ("motor_current_a", 2.5, 4.5, True),
        ("lock_time_s", 1.2, 2.6, True),
    ),
    "brakes": (
        ("cylinder_pressure_bar", 3.8, 2.4, False),
        ("pad_distance_mm", 14.0, 4.0, False),
    ),
    "hvac": (
        ("supply_return_delta_c", 8.0, 3.0, False),
        ("compressor_current_a", 6.0, 11.0, True),
    ),
    "traction": (
        ("inverter_temp_c", 55.0, 95.0, True),
        ("phase_current_a", 200.0, 350.0, True),
    ),
}


def delay_risk_minutes(failure_probability, typical_delay_minutes):
    """delay_risk = failure_probability × typical_delay_minutes"""
    probability = min(max(failure_probability, 0.0), 1.0)
    delay = max(typical_delay_minutes, 0.0)
    return round(probability * delay, 1)


def _strain(value, normal, limit, higher_is_worse):
    span = abs(limit - normal) or 1.0
    if higher_is_worse:
        moved = value - normal
    else:
        moved = normal - value
    if moved <= 0:
        return 0.0
    return moved / span


def assess(kind, values, typical_delay_minutes):
    """Use the worse of the system's measurements.

    values maps a metric name to the latest number.
    Returns health, failure probability, state, delay risk, and if-we-wait minutes.
    """
    worst = 0.0
    for metric, normal, limit, higher_is_worse in SIGNALS[kind]:
        if metric not in values:
            continue
        worst = max(worst, _strain(values[metric], normal, limit, higher_is_worse))
    strain = min(worst, 1.5)
    health = round(max(0.0, 100.0 * (1.0 - min(strain, 1.0))), 1)
    probability = round(min(0.05 + 0.45 * min(strain, 1.0), 0.9), 2)
    if health < 50:
        state = "act_tonight"
    elif health < 80:
        state = "degrading"
    else:
        state = "healthy"
    risk = delay_risk_minutes(probability, typical_delay_minutes)
    if state == "healthy":
        if_wait = risk
    else:
        if_wait = round(risk * 1.5, 1)
    return health, probability, state, risk, if_wait
