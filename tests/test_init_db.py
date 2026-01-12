from sqlalchemy import create_engine

import teleops.init_db as init_db


def test_init_db_creates_tables(monkeypatch):
    engine = create_engine("sqlite:///:memory:", future=True)
    monkeypatch.setattr(init_db, "engine", engine)
    init_db.init_db()
