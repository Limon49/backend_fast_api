"""The purchase flow — the heart of this feature."""

import pytest
from sqlmodel import Session, select

from app.crud import order as crud_order
from app.models.order import Order
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderItemCreate


def buy(client, user_id: int, *items: tuple[int, int]):
    """Helper: POST an order with ``(product_id, quantity)`` pairs."""
    return client.post(
        "/api/v1/orders",
        json={
            "user_id": user_id,
            "items": [
                {"product_id": product_id, "quantity": quantity}
                for product_id, quantity in items
            ],
        },
    )


def test_buying_a_product_saves_an_order(client, user, product):
    response = buy(client, user["id"], (product["id"], 2))

    assert response.status_code == 201
    body = response.json()

    assert body["id"] > 0
    assert body["user_id"] == user["id"]
    assert body["status"] == "paid"
    assert body["item_count"] == 1
    assert body["total_amount"] == 39.98  # 2 x 19.99
    assert body["created_at"]

    line = body["items"][0]
    assert line["product_id"] == product["id"]
    assert line["product_name"] == "FastAPI 101"  # readable, no join needed
    assert line["quantity"] == 2
    assert line["unit_price"] == 19.99
    assert line["line_total"] == 39.98

    # The customer is included too, so one GET tells the whole story.
    assert body["user"]["email"] == user["email"]


def test_the_purchase_is_visible_in_the_database(client, session, user, product):
    """What the API reports is exactly what a SQL client will find."""
    buy(client, user["id"], (product["id"], 2))

    order = session.exec(select(Order)).one()

    assert order.user_id == user["id"]
    assert order.status == "paid"
    assert float(order.total_amount) == 39.98

    line = order.items[0]
    assert line.quantity == 2
    assert float(line.unit_price) == 19.99
    assert float(line.line_total) == 39.98


def test_purchase_decreases_the_stock(client, session, user, product):
    buy(client, user["id"], (product["id"], 3))

    assert client.get(f"/api/v1/products/{product['id']}").json()["stock"] == 7
    session.expire_all()
    assert session.get(Product, product["id"]).stock == 7  # 10 - 3


def test_total_is_computed_from_the_database_price(client, user, product):
    """A client cannot talk the server into a cheaper price."""
    response = client.post(
        "/api/v1/orders",
        json={
            "user_id": user["id"],
            "items": [
                {"product_id": product["id"], "quantity": 1, "unit_price": "0.01"}
            ],
        },
    )

    assert response.status_code == 201
    assert response.json()["total_amount"] == 19.99  # the real price, not 0.01


def test_two_lines_of_the_same_product_are_merged(client, user, product):
    response = buy(client, user["id"], (product["id"], 2), (product["id"], 3))

    body = response.json()
    assert body["item_count"] == 1
    assert body["items"][0]["quantity"] == 5
    assert body["total_amount"] == 99.95  # 5 x 19.99


def test_multi_product_purchase_totals_and_decreases_each_stock(client, user, product):
    second = client.post(
        "/api/v1/products",
        json={"name": "Docker for Beginners", "price": "24.00", "stock": 4},
    ).json()

    response = buy(client, user["id"], (product["id"], 2), (second["id"], 1))

    body = response.json()
    assert body["item_count"] == 2
    assert body["total_amount"] == 63.98  # 39.98 + 24.00
    assert client.get(f"/api/v1/products/{second['id']}").json()["stock"] == 3


def test_the_price_is_snapshotted_at_purchase_time(client, user, product):
    """Changing the price later must not rewrite earlier receipts."""
    buy(client, user["id"], (product["id"], 1))

    client.patch(f"/api/v1/products/{product['id']}", json={"price": "99.00"})

    order = client.get("/api/v1/orders").json()["items"][0]
    assert order["items"][0]["unit_price"] == 19.99
    assert order["total_amount"] == 19.99


def test_not_enough_stock_is_a_conflict_and_changes_nothing(client, user, product):
    response = buy(client, user["id"], (product["id"], 999))

    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "conflict"
    assert "Not enough stock" in body["error"]["message"]
    assert "have 10" in body["error"]["message"]

    # Neither the stock nor the orders table moved.
    assert client.get(f"/api/v1/products/{product['id']}").json()["stock"] == 10
    assert client.get("/api/v1/orders").json()["total"] == 0


def test_inactive_product_cannot_be_bought(client, user, product):
    client.delete(f"/api/v1/products/{product['id']}")

    response = buy(client, user["id"], (product["id"], 1))

    assert response.status_code == 409
    assert "not available" in response.json()["error"]["message"]


def test_unknown_product_is_404(client, user):
    response = buy(client, user["id"], (999999, 1))

    assert response.status_code == 404
    assert "999999" in response.json()["error"]["message"]


def test_unknown_user_is_404(client, product):
    response = buy(client, 999999, (product["id"], 1))

    assert response.status_code == 404
    assert "User 999999" in response.json()["error"]["message"]


def test_empty_order_is_rejected(client, user):
    response = client.post("/api/v1/orders", json={"user_id": user["id"], "items": []})

    assert response.status_code == 422


def test_quantity_must_be_at_least_one(client, user, product):
    response = buy(client, user["id"], (product["id"], 0))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_cancel_puts_the_stock_back(client, user, product):
    order_id = buy(client, user["id"], (product["id"], 4)).json()["id"]
    assert client.get(f"/api/v1/products/{product['id']}").json()["stock"] == 6

    response = client.post(f"/api/v1/orders/{order_id}/cancel")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert client.get(f"/api/v1/products/{product['id']}").json()["stock"] == 10


def test_cancelling_twice_is_a_conflict_not_a_double_restock(client, user, product):
    order_id = buy(client, user["id"], (product["id"], 4)).json()["id"]
    client.post(f"/api/v1/orders/{order_id}/cancel")

    response = client.post(f"/api/v1/orders/{order_id}/cancel")

    assert response.status_code == 409
    assert client.get(f"/api/v1/products/{product['id']}").json()["stock"] == 10


def test_user_order_history(client, user, product):
    buy(client, user["id"], (product["id"], 1))
    buy(client, user["id"], (product["id"], 2))

    history = client.get(f"/api/v1/users/{user['id']}/orders").json()

    assert history["total"] == 2
    assert all(order["user_id"] == user["id"] for order in history["items"])


def test_order_history_for_unknown_user_is_404(client):
    assert client.get("/api/v1/users/999999/orders").status_code == 404


def test_orders_can_be_filtered_by_status(client, user, product):
    keep = buy(client, user["id"], (product["id"], 1)).json()["id"]
    drop = buy(client, user["id"], (product["id"], 1)).json()["id"]
    client.post(f"/api/v1/orders/{drop}/cancel")

    paid = client.get("/api/v1/orders", params={"status": "paid"}).json()
    cancelled = client.get("/api/v1/orders", params={"status": "cancelled"}).json()

    assert [order["id"] for order in paid["items"]] == [keep]
    assert [order["id"] for order in cancelled["items"]] == [drop]


def test_unknown_order_is_404(client):
    assert client.get("/api/v1/orders/999999").status_code == 404


def test_sales_report_counts_paid_orders_only(client, user, product):
    cancelled = buy(client, user["id"], (product["id"], 1)).json()["id"]
    buy(client, user["id"], (product["id"], 2))
    client.post(f"/api/v1/orders/{cancelled}/cancel")

    report = client.get("/api/v1/reports/sales").json()

    assert report["total_units"] == 2
    assert report["total_revenue"] == 39.98
    assert report["rows"][0]["product_name"] == "FastAPI 101"


def test_recent_orders_report_is_flat_and_readable(client, user, product):
    buy(client, user["id"], (product["id"], 2))

    rows = client.get("/api/v1/reports/recent-orders").json()

    assert len(rows) == 1
    row = rows[0]
    assert row["customer_name"] == user["name"]
    assert row["customer_email"] == user["email"]
    assert row["product_name"] == "FastAPI 101"
    assert row["quantity"] == 2
    assert row["line_total"] == 39.98
    assert row["order_total"] == 39.98
    assert row["status"] == "paid"


def test_a_failed_write_rolls_back_the_whole_purchase(session, user, product, monkeypatch):
    """All-or-nothing: no half-saved order, no stock taken for free.

    The failure is simulated by making ``commit`` blow up, which is exactly what
    a dropped connection or a constraint violation would do.
    """
    from sqlalchemy.exc import OperationalError

    def boom(self):
        raise OperationalError("simulated failure", None, Exception("simulated failure"))

    monkeypatch.setattr(Session, "commit", boom)

    with pytest.raises(OperationalError):
        crud_order.create_order(
            session,
            OrderCreate(
                user_id=user["id"],
                items=[OrderItemCreate(product_id=product["id"], quantity=2)],
            ),
        )

    monkeypatch.undo()
    session.expire_all()

    assert session.exec(select(Order)).all() == []
    assert session.get(Product, product["id"]).stock == 10
