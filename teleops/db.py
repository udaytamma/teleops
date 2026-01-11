"""Database setup."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from teleops.config import settings


def get_engine():
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, future=True, connect_args=connect_args)


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
