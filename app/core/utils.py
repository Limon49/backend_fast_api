"""Tiny helpers used across the app."""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Timezone-aware "now".

    ``datetime.utcnow()`` is deprecated (it returns a naive datetime, which is
    ambiguous). Storing UTC everywhere is the boring, correct choice.
    """
    return datetime.now(UTC)
