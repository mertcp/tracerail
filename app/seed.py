"""Synthetic Nordic Metro fleet. No data from real vehicles or suppliers."""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db import create_tables, get_session
from app.models import Base, Car, Component, Event, Reading, System, Train
from app.scoring import delay_risk_minutes
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
METRICS = {
    "doors": ("door_open_time_s", 2.8),
    "brakes": ("pad_wear_mm", 4.0),
    "hvac": ("supply_temp_c", 21.0),
    "traction": ("inverter_temp_c", 55.0),
}

# train number, car position, system kind -> health, failure probability, if-wait minutes
SPOTLIGHTS = {
    (7, 2, "doors"): (42.0, 0.40, 18.0, "act_tonight"),
    (3, 1, "doors"): (61.0, 0.22, 10.0, "degrading"),
    (11, 2, "doors"): (58.0, 0.25, 12.0, "degrading"),
    (9, 1, "brakes"): (64.0, 0.18, 8.0, "degrading"),
    (5, 2, "hvac"): (67.0, 0.16, 4.0, "degrading"),
    (2, 1, "traction"): (70.0, 0.14, 7.0, "degrading"),
}


def _reset() -> None:
    create_tables()
    Base.metadata.drop_all(ENGINE)
    create_tables()


def _state_for_health(health: float) -> str:
    if health < 50:
        return "act_tonight"
    if health < 80:
        return "degrading"
    return "healthy"


def _add_readings(session: Session, component: Component, kind: str, health: float) -> None:
    metric, baseline = METRICS[kind]
    drift = (100.0 - health) / 100.0
    for day in range(14):
        recorded_at = TODAY - timedelta(days=13 - day)
        progress = day / 13.0
        value = baseline * (1.0 + drift * progress)
        session.add(
            Reading(
                component=component,
                recorded_at=recorded_at,
                metric=metric,
                value=round(value, 2),
            )
        )


def seed(session: Session) -> dict:
    counts = {"trains": 0, "components": 0}
    for number in range(1, 13):
        train = Train(code="NM-{0:02d}".format(number), vehicle_class="metro")
        session.add(train)
        counts["trains"] += 1
        for position in (1, 2):
            car = Car(train=train, position=position)
            session.add(car)
            kinds = SYSTEM_KINDS if position == 1 else ("doors", "brakes", "hvac")
            for kind in kinds:
                system = System(car=car, kind=kind)
                session.add(system)
                profile = SPOTLIGHTS.get((number, position, kind))
                if profile is None:
                    health = 92.0 - ((number + position) % 5)
                    probability = 0.04
                    if_wait = 1.0
                    state = "healthy"
                else:
                    health, probability, if_wait, state = profile
                typical = TYPICAL_DELAY[kind]
                component = Component(
                    system=system,
                    name=COMPONENT_NAMES[kind],
                    state=state if profile else _state_for_health(health),
                    health_score=health,
                    failure_probability=probability,
                    typical_delay_minutes=typical,
                    delay_risk_minutes=delay_risk_minutes(probability, typical),
                    next_exam_at=TODAY + timedelta(days=21),
                    if_wait_delay_minutes=if_wait,
                )
                session.add(component)
                _add_readings(session, component, kind, health)
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
