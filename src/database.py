"""
Database setup for the learning project.

We use SQLModel (built on top of SQLAlchemy + Pydantic) with a real
MySQL server running locally on port 3306.

Connection details (defaults for a fresh Homebrew MySQL install):
  - host:     127.0.0.1
  - port:     3306
  - user:     aiquest
  - password: aiquest123
  - database: aiquest_db

You can open this same database in a GUI tool like TablePlus using
those exact settings.
"""

from sqlmodel import SQLModel, Session, create_engine

# --- Connection settings --------------------------------------------------
# We created a dedicated MySQL user for this app (more reliable than 
# root with an empty password, and works well with GUI tools like TablePlus).
DB_USER = "aiquest"
DB_PASSWORD = "aiquest123"
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_NAME = "aiquest_db"

# SQLAlchemy connection URL for MySQL using the PyMySQL driver.
# Format: mysql+pymysql://user:password@host:port/database
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# `pool_pre_ping` checks that a connection is still alive before using it,
# which avoids "server has gone away" errors on long-running apps.
engine = create_engine(DATABASE_URL, echo=True, pool_pre_ping=True)


def create_db_and_tables() -> None:
    """
    Create all tables based on SQLModel models that have `table=True`.
    Safe to call every time the app starts — it won't recreate tables
    that already exist.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    FastAPI dependency that provides a database session per request.
    Using `yield` ensures the session is properly closed afterwards,
    even if an error occurs while handling the request.
    """
    with Session(engine) as session:
        yield session
