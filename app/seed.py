"""Synthetic UK Regional fleet. No data from real vehicles or suppliers."""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db import create_tables, get_session
from app.models import Base, Car, Component, Event, Reading, Recommendation, System, Train
from app.recommend import draft
from app.scoring import SIGNALS, assess
from app.db import ENGINE

TODAY = datetime(2026, 11, 3, 8, 0, 0)
SYSTEM_KINDS = ("doors", "brakes", "hvac", "traction")
COMPONENT_NAMES = {
    "doors": "Door operator",
    "brakes": "Brake control unit",
    "hvac": "Saloon HVAC",
    "traction": "Traction inverter",
}
TYPICAL_DELAY = {"doors": 30.0, "brakes": 20.0, "hvac": 8.0, "traction": 25.0}
# Final readings for a few assets, in the same order as SIGNALS.
# Everything else stays near the normal value.
SPOTLIGHTS = {
    (7, 2, "doors"): (4.2, 2.4),
    (3, 1, "doors"): (3.4, 1.8),
    (11, 2, "doors"): (3.6, 1.9),
    (9, 1, "brakes"): (2.7, 6.0),
    (5, 2, "hvac"): (4.5, 9.0),
    (2, 1, "traction"): (82.0, 300.0),
}


def _reset() -> None:
    create_tables()
    Base.metadata.drop_all(ENGINE)
    create_tables()


def _add_readings(session: Session, component: Component, metric: str, start: float, end: float) -> None:
    for day in range(14):
        progress = day / 13.0
        value = start + (end - start) * progress
        session.add(
            Reading(
                component=component,
                recorded_at=TODAY - timedelta(days=13 - day),
                metric=metric,
                value=round(value, 2),
            )
        )


def seed(session: Session) -> dict:
    counts = {"trains": 0, "components": 0}
    for number in range(1, 13):
        train = Train(code="MM-{0:02d}".format(number), vehicle_class="metro")
        session.add(train)
        counts["trains"] += 1
        for position in (1, 2):
            car = Car(train=train, position=position)
            session.add(car)
            kinds = SYSTEM_KINDS if position == 1 else ("doors", "brakes", "hvac")
            for kind in kinds:
                system = System(car=car, kind=kind)
                session.add(system)
                signals = SIGNALS[kind]
                ends = SPOTLIGHTS.get((number, position, kind))
                values = {}
                typical = TYPICAL_DELAY[kind]
                for index, signal in enumerate(signals):
                    metric, normal, limit, higher_is_worse = signal
                    if ends is None:
                        step = ((number + position) % 3) * 0.05 * abs(limit - normal)
                        end = normal + step if higher_is_worse else normal - step
                    else:
                        end = ends[index]
                    values[metric] = end
                health, probability, state, _risk, if_wait = assess(kind, values, typical)
                component = Component(
                    system=system,
                    name=COMPONENT_NAMES[kind],
                    state=state,
                    health_score=health,
                    failure_probability=probability,
                    typical_delay_minutes=typical,
                    next_exam_at=TODAY + timedelta(days=21),
                    if_wait_delay_minutes=if_wait,
                )
                session.add(component)
                for metric, normal, _limit, _higher in signals:
                    _add_readings(session, component, metric, normal, values[metric])
                counts["components"] += 1
                if number == 7 and position == 2 and kind == "doors":
                    session.add(
                        Event(
                            component=component,
                            occurred_at=TODAY - timedelta(days=2, hours=3),
                            summary="Door failed to close at Central. Train held at the platform.",
                            caused_delay_minutes=8.0,
                        )
                    )
    for component in session.query(Component).filter(Component.state != "healthy").all():
        action, window, avoided, confidence = draft(component)
        session.add(
            Recommendation(
                component=component,
                created_at=TODAY,
                action=action,
                window=window,
                delay_minutes_avoided=avoided,
                confidence=confidence,
                status="draft",
            )
        )
    session.commit()
    return counts


def main() -> None:
    _reset()
    session = get_session()
    try:
        counts = seed(session)
    finally:
        session.close()
    print("trains={0} components={1}".format(counts["trains"], counts["components"]))


if __name__ == "__main__":
    main()
