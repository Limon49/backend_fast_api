#!/bin/sh
# Container entrypoint.
#
# 1. waits for the database and applies migrations (can be switched off with
#    RUN_MIGRATIONS=false)
# 2. hands over to the container's CMD (uvicorn by default)
#
# `exec "$@"` matters: it replaces this shell with uvicorn, so uvicorn becomes
# PID 1 and receives SIGTERM directly — that is what makes `docker stop` clean.

set -e

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "Applying database migrations (alembic upgrade head)..."
    attempts=0
    until alembic upgrade head; do
        attempts=$((attempts + 1))
        if [ "$attempts" -ge 10 ]; then
            echo "Database unreachable after $attempts attempts, giving up." >&2
            exit 1
        fi
        echo "Database not ready yet, retrying in 2s... ($attempts/10)"
        sleep 2
    done
    echo "Migrations applied."
fi

exec "$@"
