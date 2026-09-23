"""User endpoints."""


def test_create_user(client):
    response = client.post(
        "/api/v1/users",
        json={"name": "Amina", "email": "amina@example.com", "age": 31},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["name"] == "Amina"
    assert body["email"] == "amina@example.com"


def test_create_user_without_age_is_allowed(client):
    response = client.post(
        "/api/v1/users", json={"name": "Noah", "email": "noah@example.com"}
    )

    assert response.status_code == 201
    assert response.json()["age"] is None


def test_bad_email_is_rejected_with_a_clear_error(client):
    response = client.post(
        "/api/v1/users", json={"name": "Nope", "email": "not-an-email"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_duplicate_email_is_a_conflict_not_a_crash(client, user):
    response = client.post(
        "/api/v1/users",
        json={"name": "Someone else", "email": user["email"]},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_get_user(client, user):
    response = client.get(f"/api/v1/users/{user['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == user["name"]


def test_unknown_user_is_404(client):
    response = client.get("/api/v1/users/424242")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_list_users_is_paginated(client):
    for index in range(3):
        client.post(
            "/api/v1/users",
            json={"name": f"User {index}", "email": f"user{index}@example.com"},
        )

    page = client.get("/api/v1/users", params={"limit": 2}).json()

    assert page["total"] == 3
    assert page["limit"] == 2
    assert len(page["items"]) == 2

    second_page = client.get("/api/v1/users", params={"limit": 2, "offset": 2}).json()
    assert len(second_page["items"]) == 1
