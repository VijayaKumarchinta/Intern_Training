from contextlib import contextmanager
from typing import Iterator
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from config.settings import Settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None

def init_engine(settings: Settings, echo: bool = False) -> Engine:
    global _engine, _session_factory
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=2,
            pool_timeout=5,
            future=True,
        )
        _session_factory = sessionmaker(
            bind=_engine, autoflush=False, expire_on_commit=False, future=True
        )
    return _engine

def get_engine() -> Engine:
    if _engine is None:
        raise RuntimeError("Engine is not initialized.")
    return _engine

@contextmanager
def session_scope() -> Iterator[Session]:
    if _session_factory is None:
        raise RuntimeError("Session factory is not initialized.")
    session = _session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
