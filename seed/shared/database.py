"""Shared database utilities for all AutoShop services."""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

Base = declarative_base()


def get_engine(db_url: str):
    """Create a SQLAlchemy engine for the given database URL."""
    return create_engine(db_url, connect_args={"check_same_thread": False})


def get_session_factory(engine):
    """Create a session factory bound to the given engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db(session_factory) -> Generator:
    """FastAPI dependency: yields a DB session and closes it after use."""
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def init_db(engine):
    """Initialize all tables in the database."""
    Base.metadata.create_all(bind=engine)
