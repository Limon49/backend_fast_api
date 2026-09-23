"""Product endpoints — the shop shelf."""


def test_create_product(client):
    response = client.post(
        "/api/v1/products",
        json={
            "name": "SQLModel Deep Dive",
            "description": "Tables and relationships",
            "price": "29.50",
            "stock": 5,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["price"] == 29.50  # money is a JSON number, not a string
    assert body["stock"] == 5
    assert body["is_active"] is True


def test_price_must_be_positive(client):
    response = client.post(
        "/api/v1/products", json={"name": "Free lunch", "price": "0"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_stock_cannot_be_negative(client):
    response = client.post(
        "/api/v1/products", json={"name": "Weird", "price": "5.00", "stock": -1}
    )

    assert response.status_code == 422


def test_price_must_have_at_most_two_decimals(client):
    response = client.post(
        "/api/v1/products", json={"name": "Odd price", "price": "1.234"}
    )

    assert response.status_code == 422


def test_list_products_can_search_by_name(client):
    client.post("/api/v1/products", json={"name": "FastAPI 101", "price": "19.99"})
    client.post("/api/v1/products", json={"name": "Docker for Beginners", "price": "24.00"})

    page = client.get("/api/v1/products", params={"search": "fastapi"}).json()

    assert page["total"] == 1
    assert page["items"][0]["name"] == "FastAPI 101"


def test_list_products_can_filter_out_of_stock(client):
    client.post("/api/v1/products", json={"name": "Available", "price": "10.00", "stock": 3})
    client.post("/api/v1/products", json={"name": "Sold out", "price": "10.00", "stock": 0})

    in_stock = client.get("/api/v1/products", params={"in_stock": "true"}).json()
    sold_out = client.get("/api/v1/products", params={"in_stock": "false"}).json()

    assert [item["name"] for item in in_stock["items"]] == ["Available"]
    assert [item["name"] for item in sold_out["items"]] == ["Sold out"]


def test_update_only_changes_what_you_send(client, product):
    response = client.patch(
        f"/api/v1/products/{product['id']}", json={"price": "21.00", "stock": 7}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["price"] == 21.00
    assert body["stock"] == 7
    assert body["name"] == product["name"]  # untouched
    assert body["description"] is None


def test_delete_is_a_soft_delete(client, product):
    """The row stays in the database; it just leaves the shelf."""
    response = client.delete(f"/api/v1/products/{product['id']}")

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Hidden from the shop...
    assert client.get("/api/v1/products").json()["total"] == 0
    # ...but still there when you ask for it explicitly.
    assert client.get(f"/api/v1/products/{product['id']}").status_code == 200
    listed = client.get("/api/v1/products", params={"include_inactive": "true"}).json()
    assert listed["total"] == 1


def test_unknown_product_is_404(client):
    response = client.get("/api/v1/products/999999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_patching_an_unknown_product_is_404(client):
    assert client.patch("/api/v1/products/999999", json={"stock": 1}).status_code == 404
