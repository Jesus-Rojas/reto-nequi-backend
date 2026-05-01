import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def create_db_engine(database_url: str):
    connect_args = {}
    if "sqlite" in database_url:
        connect_args["check_same_thread"] = False
        if ":memory:" not in database_url:
            # Strip SQLite URI prefix to get file path
            db_path = database_url.split("///")[-1]
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
    return create_engine(database_url, connect_args=connect_args)


def _build_default_engine():
    from app.config import get_settings

    return create_db_engine(get_settings().database_url)


engine = _build_default_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
