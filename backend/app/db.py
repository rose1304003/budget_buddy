"""Database configuration and session management."""

import os
from sqlmodel import SQLModel, create_engine, Session
from .settings import settings

def _ensure_sqlite_dir(url: str) -> None:
    """Ensure the directory for SQLite database exists.
    
    Args:
        url: Database URL
    """
    if url.startswith("sqlite:///"):
        path = url.replace("sqlite:///", "", 1)
        dirpath = os.path.dirname(path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)

_ensure_sqlite_dir(settings.database_url)

engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)

def init_db() -> None:
    """Initialize database by creating all tables."""
    from . import models  # noqa
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency function to get database session.
    
    Yields:
        Database session
    """
    with Session(engine) as session:
        yield session
