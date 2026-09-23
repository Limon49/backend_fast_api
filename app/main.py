"""
The FastAPI application.

``create_app()`` builds the app: logging, CORS, error handling, and the routers.
Keeping it a function (instead of module-level side effects) is what makes the
app testable — the tests build the same app and swap the database out.

Run it with::

    uv run uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.database import create_db_and_tables
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown work.

    Note what happens *not* here: no table creation by default. Migrations
    (``uv run python -m app.scripts.init_db``) own the schema, so two app
    instances starting at once cannot race each other. Set
    ``AUTO_CREATE_TABLES=true`` if you want the old convenience behaviour back.
    """
    settings = get_settings()
    configure_logging()
    logger.info("Starting %s v%s (%s)", settings.app_name, settings.app_version, settings.environment)

    if settings.auto_create_tables:
        logger.warning("AUTO_CREATE_TABLES is on: creating tables from the models")
        create_db_and_tables()

    yield

    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Build and configure the application."""
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "A small e-commerce style API: users buy products and every purchase "
            "is stored in the database. Interactive docs: /docs"
        ),
        lifespan=lifespan,
    )

    # Let a browser app talk to this API from another origin.
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # One consistent error shape for every failure.
    register_exception_handlers(application)

    # All resources live under /api/v1.
    application.include_router(api_router, prefix=settings.api_v1_prefix)

    @application.get("/", tags=["root"], summary="Welcome")
    def read_root() -> dict:
        """Where to go next, so nobody has to guess."""
        return {
            "message": "Welcome to AIQuest!",
            "docs": "/docs",
            "api": settings.api_v1_prefix,
            "health": f"{settings.api_v1_prefix}/health",
        }

    return application


app = create_app()
