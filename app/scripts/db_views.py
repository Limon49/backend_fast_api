"""
The ``order_details`` SQL view.

A view is a saved query that behaves like a table. Without it, answering "who
bought what?" means joining four tables by hand every time::

    SELECT * FROM order_details;

...and you get one flat, readable row per order line, straight in TablePlus or
the MySQL client. ``GET /api/v1/reports/recent-orders`` returns the same shape.
"""

from sqlalchemy import Engine, text

from app.core.database import engine

ORDER_DETAILS_VIEW = "order_details"

# `user` is backticked because USER is a keyword in MySQL.
CREATE_ORDER_DETAILS_VIEW_SQL = f"""
CREATE VIEW {ORDER_DETAILS_VIEW} AS
SELECT
    oi.id           AS order_item_id,
    o.id            AS order_id,
    u.name          AS customer_name,
    u.email         AS customer_email,
    p.id            AS product_id,
    p.name          AS product_name,
    oi.quantity     AS quantity,
    oi.unit_price   AS unit_price,
    oi.line_total   AS line_total,
    o.total_amount  AS order_total,
    o.status        AS status,
    o.created_at    AS created_at
FROM order_item AS oi
JOIN orders AS o      ON o.id = oi.order_id
JOIN `user` AS u      ON u.id = o.user_id
JOIN product AS p     ON p.id = oi.product_id
"""


def create_views(target_engine: Engine = engine) -> list[str]:
    """(Re)create every reporting view. Safe to run as often as you like.

    ``DROP VIEW IF EXISTS`` + ``CREATE VIEW`` works on MySQL and SQLite alike
    (SQLite has no ``CREATE OR REPLACE VIEW``).
    """
    with target_engine.begin() as connection:
        connection.execute(text(f"DROP VIEW IF EXISTS {ORDER_DETAILS_VIEW}"))
        connection.execute(text(CREATE_ORDER_DETAILS_VIEW_SQL))
    return [ORDER_DETAILS_VIEW]


def main() -> None:  # pragma: no cover - manual helper
    created = create_views()
    print(f"Created view(s): {', '.join(created)}")
    print(f"Try it:  SELECT * FROM {ORDER_DETAILS_VIEW};")


if __name__ == "__main__":  # pragma: no cover
    main()
