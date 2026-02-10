"""Initialize database tables."""

from sqlalchemy import inspect, text

from teleops.db import engine
from teleops.models import Base

_RCA_MIGRATIONS = [
    ("duration_ms", "ALTER TABLE rca_artifacts ADD COLUMN duration_ms FLOAT"),
    ("status", "ALTER TABLE rca_artifacts ADD COLUMN status VARCHAR(24) DEFAULT 'pending_review'"),
    ("reviewed_by", "ALTER TABLE rca_artifacts ADD COLUMN reviewed_by VARCHAR(128)"),
    ("reviewed_at", "ALTER TABLE rca_artifacts ADD COLUMN reviewed_at DATETIME"),
]


def _migrate_rca_artifacts(connection) -> None:
    """Add new columns to rca_artifacts if they don't exist (SQLite)."""
    inspector = inspect(connection)
    if "rca_artifacts" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("rca_artifacts")}
    for col_name, ddl in _RCA_MIGRATIONS:
        if col_name not in existing:
            connection.execute(text(ddl))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        _migrate_rca_artifacts(conn)
        conn.commit()


if __name__ == "__main__":
    init_db()
