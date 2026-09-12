"""SQLModel relational storage — config, state, signals."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class SignalRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str
    exchange: str
    signal_type: str
    strength: str
    confidence: float
    direction: str
    timestamp: datetime
    details: str | None = None


class NewsRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source: str
    title: str
    url: str
    published_at: datetime
    sentiment: float | None = None
    assets: str | None = None


def init_db(database_url: str = "sqlite:///pulse.db") -> None:
    from sqlmodel import SQLModel
    from sqlalchemy import create_engine
    engine = create_engine(database_url, echo=False)
    SQLModel.metadata.create_all(engine)
    return engine

engine = None  # initialized at startup
