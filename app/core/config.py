"""
Application configuration.

Every value below can be overridden with an environment variable (or a line in
a local ``.env`` file). That is what makes the same code run against your local
MySQL, a Docker container, or a hosted database without editing any Python.

Quick example::

    export DB_HOST=db          # docker-compose service name
    export SQL_ECHO=true       # print every SQL statement
"""

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All settings for the app, loaded from environment variables / ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application -----------------------------------------------------
    app_name: str = "AIQuest API"
    app_version: str = "0.2.0"
    environment: str = "development"  # development | production | test
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # --- Database --------------------------------------------------------
    # Defaults match the local Homebrew MySQL used by this project.
    db_user: str = "aiquest"
    db_password: str = "aiquest123"
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str = "aiquest_db"

    # Full connection URL override. When set it wins over the DB_* values
    # above, which is handy for CI or one-off script runs.
    database_url_override: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL", "database_url_override"),
    )

    # Log every SQL statement (very noisy: development only).
    sql_echo: bool = False

    # Create tables straight from the models on startup instead of running
    # migrations. Handy for a quick experiment, OFF by default because
    # Alembic migrations are the source of truth.
    auto_create_tables: bool = False

    # --- CORS ------------------------------------------------------------
    # Comma separated list: "http://localhost:3000,https://app.example.com".
    cors_origins: str = "*"

    @property
    def sqlalchemy_url(self) -> str:
        """The SQLAlchemy connection URL, e.g. mysql+pymysql://user:pw@host/db."""
        if self.database_url_override:
            return self.database_url_override
        return (
            f"mysql+pymysql://{self.db_user}:{quote_plus(self.db_password)}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        """``cors_origins`` split into a list, ignoring empty entries."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return the settings object (built once, then reused everywhere)."""
    return Settings()
