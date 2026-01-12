import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from teleops.api.app import app, get_db
from teleops.models import Base


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    token = getattr(__import__("teleops.config", fromlist=["settings"]).settings, "api_token", None)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides = {}
    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient

    client = TestClient(app)
    if token:
        client.headers.update({"X-API-Key": token})
    return client
