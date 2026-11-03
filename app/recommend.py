"""One JSON model call drafts maintenance from the asset's measurements.

The component sends currents, times, pressures, and temperatures.
TraceRail scores health and delay risk for the fleet rank.
The model reviews those numbers and picks the work for the upcoming days.
Without OPENAI_API_KEY, the same numbers drive a plain rule draft.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from app.scoring import SIGNALS

WINDOWS = ("tonight", "within 3 days", "before the next exam")


def _measurements(component):
    ordered = sorted(component.readings, key=lambda item: item.recorded_at)
    by_metric = {}
    for reading in ordered:
        by_metric.setdefault(reading.metric, {"from": reading.value})
        by_metric[reading.metric]["to"] = reading.value
    described = []
    for metric, normal, limit, higher_is_worse in SIGNALS[component.system.kind]:
        sample = by_metric.get(metric, {})
        described.append({
            "metric": metric,
            "from": sample.get("from"),
            "to": sample.get("to"),
            "normal": normal,
            "limit": limit,
            "higher_is_worse": higher_is_worse,
        })
    return described


def brief(component):
    """Bundle the inputs the model is allowed to use."""
    system = component.system
    car = system.car
    events = [
        {
            "summary": event.summary,
            "caused_delay_minutes": event.caused_delay_minutes,
            "at": event.occurred_at.isoformat(),
        }
        for event in sorted(component.events, key=lambda item: item.occurred_at)[-3:]
    ]
    return {
        "train": car.train.code,
        "car": car.position,
        "system": system.kind,
        "component": component.name,
        "measurements": _measurements(component),
        "failure_probability": component.failure_probability,
        "typical_delay_minutes": component.typical_delay_minutes,
        "delay_risk_minutes": component.delay_risk_minutes,
        "if_wait_delay_minutes": component.if_wait_delay_minutes,
        "next_exam_at": component.next_exam_at.isoformat() if component.next_exam_at else None,
        "recent_events": events,
    }


def draft_from_rules(component):
    """Fallback when no API key or the model call fails."""
    name = component.name.lower()
    risk = component.delay_risk_minutes
    waiting = component.if_wait_delay_minutes
    if component.state == "act_tonight":
        return (
            "Inspect the {0} tonight. About {1:g} delay minutes can be avoided.".format(name, risk),
            "tonight",
            risk,
            0.8,
        )
    if component.state == "degrading":
        return (
            "Schedule the {0} within 3 days. Waiting leaves about {1:g} delay minutes at risk.".format(
                name, waiting
            ),
            "within 3 days",
            risk,
            0.6,
        )
    return (
        "Leave the {0} in service until the next exam.".format(name),
        "before the next exam",
        risk,
        0.5,
    )


def _parse(payload):
    action = str(payload.get("action", "")).strip()
    window = str(payload.get("window", "")).strip()
    if window not in WINDOWS:
        window = "before the next exam"
    avoided = float(payload.get("delay_minutes_avoided", 0))
    confidence = float(payload.get("confidence", 0.7))
    if not action:
        raise ValueError("empty action")
    return action, window, avoided, max(0.0, min(confidence, 1.0))


def draft_from_llm(component):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    body = {
        "model": os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "You plan railway maintenance from sensor readings. "
                    "The component did not say it is healthy or that it needs work. "
                    "Review the measurements against normal and limit, plus the delay-risk numbers. "
                    "Decide the maintenance needed in the upcoming days. "
                    "Reply with JSON keys action, window, delay_minutes_avoided, confidence. "
                    "window must be tonight, within 3 days, or before the next exam. "
                    "action is one sentence a maintainer can accept or edit. "
                    "delay_minutes_avoided should stay close to delay_risk_minutes. "
                    "confidence is a number from 0 to 1."
                ),
            },
            {"role": "user", "content": json.dumps(brief(component))},
        ],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {0}".format(api_key),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = json.loads(response.read().decode("utf-8"))
        content = raw["choices"][0]["message"]["content"]
        return _parse(json.loads(content))
    except (urllib.error.URLError, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        return None


def draft(component):
    from_model = draft_from_llm(component)
    if from_model is not None:
        return from_model
    return draft_from_rules(component)
