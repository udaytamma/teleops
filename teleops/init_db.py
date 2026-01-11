"""Initialize database tables."""

from teleops.db import engine
from teleops.models import Base


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
