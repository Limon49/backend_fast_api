"""AIQuest API application package.

Layout
------
``app/main.py``      the FastAPI application (factory + router wiring)
``app/core/``        configuration, database engine, errors, logging
``app/models/``      SQLModel *table* models (what the database really stores)
``app/schemas/``     request/response contracts (what the API sends and accepts)
``app/crud/``        database access + business rules (no HTTP in here)
``app/api/v1/``      HTTP layer: routers, one file per resource
``app/scripts/``     one-off helpers (seed data, SQL views, migrations runner)
"""
