"""Reporting contracts.

``OrderDetailRead`` deliberately mirrors the columns of the ``order_details``
SQL view (see ``app/scripts/db_views.py``), so the API and the database tell
exactly the same story.
"""

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import Money


class SalesRow(BaseModel):
    """One product's sales figures."""

    product_id: int
    product_name: str
    units_sold: int
    revenue: Money


class SalesReport(BaseModel):
    """``GET /api/v1/reports/sales``."""

    total_revenue: Money
    total_units: int
    rows: list[SalesRow]


class OrderDetailRead(BaseModel):
    """One flat row: the same shape as ``SELECT * FROM order_details;``."""

    order_item_id: int
    order_id: int
    customer_name: str
    customer_email: str
    product_id: int
    product_name: str
    quantity: int
    unit_price: Money
    line_total: Money
    order_total: Money
    status: str
    created_at: datetime
