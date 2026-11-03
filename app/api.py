"""Fleet API. Recommendation text is written from the delay-risk numbers."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.db import create_tables, get_session
from app.models import Car, Component, Event, Recommendation, System, Train
from app.seed import seed

app = FastAPI(title="TraceRail", version="0.1.0")


def session_scope():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


@app.on_event("startup")
def startup():
    create_tables()
    session = get_session()
    try:
        if session.query(Train).count() == 0:
            seed(session)
    finally:
        session.close()


def _asset(component):
    system = component.system
    car = system.car
    return {
        "id": component.id,
        "train": car.train.code,
        "car": car.position,
        "system": system.kind,
        "component": component.name,
        "state": component.state,
        "health_score": component.health_score,
        "failure_probability": component.failure_probability,
        "typical_delay_minutes": component.typical_delay_minutes,
        "delay_risk_minutes": component.delay_risk_minutes,
        "if_wait_delay_minutes": component.if_wait_delay_minutes,
        "formula": "delay_risk = failure_probability × typical_delay_minutes",
    }


def _one(session, component_id):
    component = (
        session.query(Component)
        .options(
            joinedload(Component.system).joinedload(System.car).joinedload(Car.train),
            joinedload(Component.readings),
            joinedload(Component.events),
            joinedload(Component.recommendations),
        )
        .filter(Component.id == component_id)
        .one_or_none()
    )
    if component is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return component


def _draft(component):
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
            "Schedule the {0} before the next exam. Waiting leaves about {1:g} delay minutes at risk.".format(
                name, waiting
            ),
            "before the next exam",
            risk,
            0.6,
        )
    return (
        "Leave the {0} in service until the next exam.".format(name),
        "next exam",
        risk,
        0.5,
    )


class EventIn(BaseModel):
    summary: str
    caused_delay_minutes: float = 0


class DecisionIn(BaseModel):
    status: str
    edited_action: Optional[str] = None


@app.get("/")
def home():
    page = Path(__file__).resolve().parent / "fleet.html"
    return FileResponse(page)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/fleet")
def fleet(session: Session = Depends(session_scope)):
    components = (
        session.query(Component)
        .options(joinedload(Component.system).joinedload(System.car).joinedload(Car.train))
        .all()
    )
    rows = [_asset(component) for component in components]
    rows.sort(key=lambda row: row["delay_risk_minutes"], reverse=True)
    return rows


@app.get("/assets/{component_id}")
def asset(component_id: int, session: Session = Depends(session_scope)):
    component = _one(session, component_id)
    body = _asset(component)
    body["readings"] = [
        {"at": reading.recorded_at.isoformat(), "metric": reading.metric, "value": reading.value}
        for reading in sorted(component.readings, key=lambda item: item.recorded_at)
    ]
    body["events"] = [
        {
            "at": event.occurred_at.isoformat(),
            "summary": event.summary,
            "caused_delay_minutes": event.caused_delay_minutes,
        }
        for event in sorted(component.events, key=lambda item: item.occurred_at)
    ]
    body["recommendations"] = [
        {
            "id": item.id,
            "action": item.edited_action or item.action,
            "window": item.window,
            "delay_minutes_avoided": item.delay_minutes_avoided,
            "confidence": item.confidence,
            "status": item.status,
        }
        for item in component.recommendations
    ]
    return body


@app.post("/assets/{component_id}/events")
def add_event(component_id: int, incoming: EventIn, session: Session = Depends(session_scope)):
    component = _one(session, component_id)
    event = Event(
        component=component,
        occurred_at=datetime.now(),
        summary=incoming.summary,
        caused_delay_minutes=incoming.caused_delay_minutes,
    )
    session.add(event)
    session.commit()
    return {"id": event.id, "summary": event.summary, "caused_delay_minutes": event.caused_delay_minutes}


@app.post("/assets/{component_id}/recommend")
def recommend(component_id: int, session: Session = Depends(session_scope)):
    component = _one(session, component_id)
    action, window, avoided, confidence = _draft(component)
    record = Recommendation(
        component=component,
        created_at=datetime.now(),
        action=action,
        window=window,
        delay_minutes_avoided=avoided,
        confidence=confidence,
        status="draft",
    )
    session.add(record)
    session.commit()
    return {
        "id": record.id,
        "action": record.action,
        "window": record.window,
        "delay_minutes_avoided": record.delay_minutes_avoided,
        "confidence": record.confidence,
        "status": record.status,
    }


@app.post("/recommendations/{recommendation_id}/decision")
def decide(recommendation_id: int, incoming: DecisionIn, session: Session = Depends(session_scope)):
    if incoming.status not in ("accepted", "edited", "rejected"):
        raise HTTPException(status_code=400, detail="Status must be accepted, edited, or rejected")
    record = session.get(Recommendation, recommendation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    record.status = incoming.status
    if incoming.status == "edited":
        if not incoming.edited_action:
            raise HTTPException(status_code=400, detail="An edited action is required")
        record.edited_action = incoming.edited_action
    session.commit()
    return {
        "id": record.id,
        "action": record.edited_action or record.action,
        "window": record.window,
        "delay_minutes_avoided": record.delay_minutes_avoided,
        "status": record.status,
    }
