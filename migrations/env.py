"""
Alembic environment.

Alembic's job: compare the SQLModel models with the real database and apply the
differences as migration scripts.

Two things worth knowing:

* the connection URL is **not** in ``alembic.ini`` — it is read from the app
  settings, so migrations and the API can never disagree about the database;
* ``target_metadata`` is SQLModel's metadata, which only sees the tables that
  have been imported, hence ``import app.models`` below.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine
from sqlmodel import SQLModel

import app.models  # noqa: F401  (importing registers every table)
from app.core.config import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

#: The models are the source of truth for ``--autogenerate``.
target_metadata = SQLModel.metadata


def get_url() -> str:
    """The database to migrate (honours DATABASE_URL / .env / defaults)."""
    return get_settings().sqlalchemy_url


def run_migrations_offline() -> None:
    """Emit SQL without connecting: ``alembic upgrade head --sql``."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect and apply the migrations."""
    url = get_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
