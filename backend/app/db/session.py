"""Engine and session management.

SQLite with a typed graph built in Python, not a graph database (docs/ARCHITECTURE.md
section 25). `check_same_thread=False` is required because FastAPI serves requests from
a thread pool while the demo database is a single local file.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

from .base import Base

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

ENGINE: Engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)

SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, expire_on_commit=False, future=True)


@event.listens_for(ENGINE, "connect")
def _enable_foreign_keys(dbapi_connection, _record) -> None:  # pragma: no cover - driver hook
    """SQLite ignores foreign keys unless asked. Graph invariants depend on them."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_all() -> None:
    # Import for side effect: model modules must be loaded before metadata is complete.
    from app import models  # noqa: F401

    Base.metadata.create_all(ENGINE)


def drop_all() -> None:
    from app import models  # noqa: F401

    Base.metadata.drop_all(ENGINE)


@contextmanager
def session_scope() -> Iterator[Session]:
    """Transactional scope for scripts and services."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Iterator[Session]:
    """FastAPI dependency. Read endpoints do not write, so no commit here."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
