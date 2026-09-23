"""
Bring the database up to date in one command.

    uv run python -m app.scripts.init_db

It runs every pending migration and then (re)creates the reporting view. Run it
after pulling changes, and once before starting the server for the first time.

Deployments usually run ``alembic upgrade head`` as their own step instead; see
the README.
"""

from alembic import command
from alembic.config import Config

from app.core.config import get_settings
from app.scripts.db_views import create_views

ALEMBIC_INI = "alembic.ini"


def main() -> None:  # pragma: no cover - manual helper
    settings = get_settings()
    print(f"Database: {settings.sqlalchemy_url}")

    config = Config(ALEMBIC_INI)
    command.upgrade(config, "head")

    created = create_views()
    print(f"Migrations applied. View(s) ready: {', '.join(created)}")


if __name__ == "__main__":  # pragma: no cover
    main()
