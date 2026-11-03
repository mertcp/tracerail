"""SQLite database for the local demo. Postgres can replace the URL later."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "tracerail.db"
ENGINE = create_engine(
    "sqlite:///{0}".format(DB_PATH),
    future=True,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=ENGINE, expire_on_commit=False)


def create_tables() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(ENGINE)


def get_session() -> Session:
    return SessionLocal()
