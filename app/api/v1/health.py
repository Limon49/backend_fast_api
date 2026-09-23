"""Health endpoint, used by Docker, load balancers and monitoring."""

from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlmodel import Session

from app.api.deps import SessionDep
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
def health(response: Response, session: SessionDep) -> dict:
    """Report whether the app is up **and** whether it can reach the database.

    A quick ``SELECT 1`` is a real test: the app could be running happily while
    pointing at a database that no longer answers. Returns 503 when the
    database is unreachable so orchestrators can act on it.
    """
    settings = get_settings()

    database = "ok"
    try:
        session.exec(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - depends on a broken database
        database = f"error: {exc}"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if database == "ok" else "degraded",
        "environment": settings.environment,
        "version": settings.app_version,
        "database": database,
    }
