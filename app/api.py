"""Fleet API. Recommend uses one model call over scored measurements."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.db import create_tables, get_session
from app.models import Car, Component, Event, Reading, Recommendation, System, Train
from app.locations import TRAIN_LOCATIONS
from app.maintenance_plan import action_text, sections as maintenance_sections
from app.recommend import draft
from app.scoring import assess
from app.seed import seed

app = FastAPI(
    title="TraceRail",
    description="Condition-based maintenance demo — delay-risk ranked fleet, synthetic UK Regional.",
    version="0.1.0",
)

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
        "if_wait_delay_minutes": component.if_wait_delay_minutes,
        "formula": "failure_probability × typical_delay_minutes",
        "location": TRAIN_LOCATIONS.get(car.train.code, "Unknown depot"),
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


class EventIn(BaseModel):
    summary: str
    caused_delay_minutes: float = 0


class ReadingIn(BaseModel):
    metric: str
    value: float


@app.get("/")
def home():
    page = Path(__file__).resolve().parent / "fleet.html"
    return FileResponse(page, headers={"Cache-Control": "no-cache"})


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
    rows.sort(key=lambda row: (row["health_score"], -row["failure_probability"]))
    return rows


@app.get("/maintenance-drafts")
def maintenance_drafts(session: Session = Depends(session_scope)):
    components = (
        session.query(Component)
        .options(
            joinedload(Component.system).joinedload(System.car).joinedload(Car.train),
            joinedload(Component.recommendations),
        )
        .filter(Component.state != "healthy")
        .all()
    )
    components.sort(key=lambda item: (item.health_score, -item.failure_probability))
    rows = []
    for component in components:
        car = component.system.car
        plan = maintenance_sections(component)
        latest = sorted(component.recommendations, key=lambda item: item.created_at)[-1] if component.recommendations else None
        rows.append({
            "component_id": component.id,
            "train": car.train.code,
            "car": car.position,
            "system": component.system.kind,
            "component": component.name,
            "state": component.state,
            "health_score": component.health_score,
            "location": TRAIN_LOCATIONS.get(car.train.code, "Unknown depot"),
            "summary": plan["summary"],
            "depot": plan["depot"],
            "duration": plan["duration"],
            "crew": plan["crew"],
            "documentation": plan["documentation"],
            "action": (latest.edited_action or latest.action) if latest else action_text(component),
            "window": latest.window if latest else "tonight",
            "status": latest.status if latest else "draft",
            "recommendation_id": latest.id if latest else None,
        })
    return rows


@app.get("/assets/{component_id}")
def asset(component_id: int, session: Session = Depends(session_scope)):
    component = _one(session, component_id)
    body = _asset(component)
    body["maintenance"] = maintenance_sections(component)
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


@app.post("/assets/{component_id}/readings")
def add_reading(component_id: int, incoming: ReadingIn, session: Session = Depends(session_scope)):
    component = _one(session, component_id)
    session.add(
        Reading(
            component=component,
            recorded_at=datetime.now(),
            metric=incoming.metric,
            value=incoming.value,
        )
    )
    _apply(component)
    session.commit()
    return {"metric": incoming.metric, "value": incoming.value, "state": component.state}


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


def _apply(component):
    values = {}
    for reading in sorted(component.readings, key=lambda item: item.recorded_at):
        values[reading.metric] = reading.value
    health, probability, state, _risk, if_wait = assess(
        component.system.kind, values, component.typical_delay_minutes
    )
    component.health_score = health
    component.failure_probability = probability
    component.state = state
    component.if_wait_delay_minutes = if_wait


@app.post("/assets/{component_id}/recommend")
def recommend(component_id: int, session: Session = Depends(session_scope)):
    component = _one(session, component_id)
    action, window, avoided, confidence = draft(component)
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

