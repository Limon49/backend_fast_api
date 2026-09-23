"""
Database engine and session handling.

This module is the single place that knows how to talk to the database. Routers
never build their own connections: they ask FastAPI for a session through
``app.api.deps.SessionDep``.
"""

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings

settings = get_settings()

# ``pool_pre_ping`` checks that a pooled connection is still alive before using
# it, which avoids "server has gone away" errors on long-running apps.
engine = create_engine(
    settings.sqlalchemy_url,
    echo=settings.sql_echo,
    pool_pre_ping=True,
)


def create_db_and_tables() -> None:
    """Create every table from the models.

    Convenience for quick experiments (``AUTO_CREATE_TABLES=true``). Real
    projects use migrations instead: see ``app/scripts/init_db.py``.
    """
    import app.models  # noqa: F401  (importing registers every table)

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that provides one database session per request.

    Using ``yield`` guarantees the session is closed afterwards, even when the
    request fails part-way through.
    """
    with Session(engine) as session:
        yield session
