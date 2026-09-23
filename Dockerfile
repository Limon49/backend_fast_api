# ---- Build stage: install dependencies with uv ----
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

WORKDIR /app

# Copy dependency files first so Docker can cache this layer
COPY pyproject.toml uv.lock ./

# Install dependencies into /app/.venv (tests are dev-only, so they don't ship)
RUN uv sync --frozen --no-install-project --no-dev

# ---- Runtime stage: a small, clean final image ----
FROM python:3.14-slim-bookworm

# PYTHONDONTWRITEBYTECODE: no .pyc clutter
# PYTHONUNBUFFERED:      logs appear immediately instead of being buffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# The virtualenv built in the previous stage
COPY --from=builder /app/.venv /app/.venv

# Application code, migrations, and the entrypoint
COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run as a non-root user: if the app is ever compromised, the damage is limited.
RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && chown -R app:app /app
USER app

EXPOSE 8000

# The platform can ask "are you alive?" without guessing at your routes.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3).status == 200 else 1)"

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
