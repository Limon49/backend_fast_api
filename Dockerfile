# ---- Build stage: install dependencies with uv ----
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS builder

WORKDIR /app

# Copy dependency files first so Docker can cache this layer
COPY pyproject.toml uv.lock ./

# Install dependencies into the system Python (no venv needed in a container)
RUN uv sync --frozen --no-install-project --no-dev

# ---- Runtime stage: a small, clean final image ----
FROM python:3.14-slim-bookworm

WORKDIR /app

# Copy the installed packages from the build stage
COPY --from=builder /app/.venv /app/.venv

# Copy the application code
COPY main.py ./

# Make the virtualenv's commands available
ENV PATH="/app/.venv/bin:$PATH"

# Run one worker per container; the platform handles scaling
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
