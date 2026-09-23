"""The app must be reachable, and so must the database."""


def test_root_points_at_the_docs(client):
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["docs"] == "/docs"
    assert body["api"] == "/api/v1"


def test_health_reports_the_database(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_openapi_schema_is_generated(client):
    """A cheap guard: bad response models break the docs before they break prod."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    for path in ("/api/v1/products", "/api/v1/orders", "/api/v1/reports/sales"):
        assert path in paths
