from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from teleops.api.app import app, get_db
from teleops.models import Base


def test_generate_and_list_incidents():
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides = {}
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)

    resp = client.post("/generate", json={"alert_rate_per_min": 5, "duration_min": 3, "noise_rate_per_min": 1})
    assert resp.status_code == 200

    incidents = client.get("/incidents").json()
    assert len(incidents) >= 1
