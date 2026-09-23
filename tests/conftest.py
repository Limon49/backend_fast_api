"""
Shared pytest fixtures.

Tests run against a throwaway SQLite file, **never** your MySQL database, so
``uv run pytest`` cannot damage real data.

The trick is ``app.dependency_overrides``: the tests swap out the "give me a
database session" dependency for one that points at the test database. No
application code is modified, mocked at import time, or made conditional.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401  (registers every table before create_all)
from app.core.database import get_session
from app.main import app


@pytest.fixture(name="engine")
def engine_fixture(tmp_path):
    """A brand new, empty database for every single test."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'test.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(name="session")
def session_fixture(engine):
    """A session for tests that want to check the database directly."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(engine):
    """The API, connected to the test database."""

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(name="user")
def user_fixture(client) -> dict:
    """A saved user (created through the API, so the whole stack is exercised)."""
    response = client.post(
        "/api/v1/users",
        json={"name": "Limon", "email": "limon@edutune.com", "age": 25},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture(name="product")
def product_fixture(client) -> dict:
    """A saved product with 10 in stock."""
    response = client.post(
        "/api/v1/products",
        json={"name": "FastAPI 101", "price": "19.99", "stock": 10},
    )
    assert response.status_code == 201, response.text
    return response.json()
