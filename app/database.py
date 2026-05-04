import os
from abc import ABC, abstractmethod
from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


# ── Database engine adapters ──────────────────────────────────────────────────

class DatabaseEngineAdapter(ABC):
    """Contrato para construir un engine de SQLAlchemy según el motor de BD."""

    @abstractmethod
    def build(self, database_url: str) -> Engine: ...


class SQLiteEngineAdapter(DatabaseEngineAdapter):
    def build(self, database_url: str) -> Engine:
        if ":memory:" in database_url:
            return self._create_engine(database_url)

        db_path = database_url.split("///")[-1]
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(name=db_dir, exist_ok=True)

        return self._create_engine(database_url)

    def _create_engine(self, database_url: str) -> Engine:
        return create_engine(url=database_url, connect_args={"check_same_thread": False})


class DefaultEngineAdapter(DatabaseEngineAdapter):
    def build(self, database_url: str) -> Engine:
        return create_engine(url=database_url)


def _resolve_adapter(database_url: str) -> DatabaseEngineAdapter:
    if "sqlite" in database_url:
        return SQLiteEngineAdapter()
    return DefaultEngineAdapter()


def create_db_engine(database_url: str) -> Engine:
    return _resolve_adapter(database_url).build(database_url)


def _build_default_engine() -> Engine:
    return create_db_engine(get_settings().database_url)


engine = _build_default_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
