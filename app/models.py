"""Operational fleet twin: train → car → system → component, plus history."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Train(Base):
    __tablename__ = "trains"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(16), unique=True)  # MM-07
    vehicle_class: Mapped[str] = mapped_column(String(32), default="metro")

    cars: Mapped[list["Car"]] = relationship(back_populates="train")


class Car(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(primary_key=True)
    train_id: Mapped[int] = mapped_column(ForeignKey("trains.id"))
    position: Mapped[int] = mapped_column(Integer)  # 1..n along the train

    train: Mapped[Train] = relationship(back_populates="cars")
    systems: Mapped[list["System"]] = relationship(back_populates="car")


class System(Base):
    """One system on one car, e.g. doors of car 3."""

    __tablename__ = "systems"

    id: Mapped[int] = mapped_column(primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"))
    kind: Mapped[str] = mapped_column(String(32))  # doors, brakes, hvac, traction

    car: Mapped[Car] = relationship(back_populates="systems")
    components: Mapped[list["Component"]] = relationship(back_populates="system")


class Component(Base):
    """The asset we score. Health and delay risk live here."""

    __tablename__ = "components"

    id: Mapped[int] = mapped_column(primary_key=True)
    system_id: Mapped[int] = mapped_column(ForeignKey("systems.id"))
    name: Mapped[str] = mapped_column(String(80))
    # healthy, degrading, act_tonight
    state: Mapped[str] = mapped_column(String(32), default="healthy")
    health_score: Mapped[float] = mapped_column(Float, default=100)
    failure_probability: Mapped[float] = mapped_column(Float, default=0)
    typical_delay_minutes: Mapped[float] = mapped_column(Float, default=0)
    next_exam_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # Expected delay minutes if the asset stays in service until next_exam_at.
    if_wait_delay_minutes: Mapped[float] = mapped_column(Float, default=0)

    system: Mapped[System] = relationship(back_populates="components")
    readings: Mapped[list["Reading"]] = relationship(back_populates="component")
    events: Mapped[list["Event"]] = relationship(back_populates="component")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="component")


class Reading(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(primary_key=True)
    component_id: Mapped[int] = mapped_column(ForeignKey("components.id"))
    recorded_at: Mapped[datetime] = mapped_column(DateTime)
    metric: Mapped[str] = mapped_column(String(64))
    value: Mapped[float] = mapped_column(Float)

    component: Mapped[Component] = relationship(back_populates="readings")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    component_id: Mapped[int] = mapped_column(ForeignKey("components.id"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime)
    summary: Mapped[str] = mapped_column(Text)
    caused_delay_minutes: Mapped[float] = mapped_column(Float, default=0)

    component: Mapped[Component] = relationship(back_populates="events")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    component_id: Mapped[int] = mapped_column(ForeignKey("components.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    action: Mapped[str] = mapped_column(Text)
    window: Mapped[str] = mapped_column(String(64))
    delay_minutes_avoided: Mapped[float] = mapped_column(Float, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    # draft, accepted, edited, rejected
    status: Mapped[str] = mapped_column(String(32), default="draft")
    edited_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    component: Mapped[Component] = relationship(back_populates="recommendations")
