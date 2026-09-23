"""Reporting endpoints — the same numbers you would query in SQL."""

from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.crud import report as crud_report
from app.schemas.report import OrderDetailRead, SalesReport, SalesRow

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/sales", response_model=SalesReport, summary="Units sold + revenue per product")
def sales_report(session: SessionDep) -> SalesReport:
    """Best sellers first. Cancelled orders are excluded."""
    rows = [
        SalesRow(
            product_id=product_id,
            product_name=product_name,
            units_sold=units_sold,
            revenue=revenue,
        )
        for product_id, product_name, units_sold, revenue in crud_report.sales_by_product(
            session
        )
    ]

    return SalesReport(
        total_revenue=sum((row.revenue for row in rows), start=Decimal("0.00")),
        total_units=sum(row.units_sold for row in rows),
        rows=rows,
    )


@router.get(
    "/recent-orders",
    response_model=list[OrderDetailRead],
    summary="Flat, human-readable view of recent purchases",
)
def recent_orders(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200, description="How many rows")] = 50,
) -> list[OrderDetailRead]:
    """One row per order line: who bought what, how many, at what price.

    Identical in shape to ``SELECT * FROM order_details;`` in the database, so
    the API and TablePlus never disagree.
    """
    return [
        OrderDetailRead(
            order_item_id=order_item_id,
            order_id=order_id,
            customer_name=customer_name,
            customer_email=customer_email,
            product_id=product_id,
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            line_total=line_total,
            order_total=order_total,
            status=order_status,
            created_at=created_at,
        )
        for (
            order_item_id,
            order_id,
            customer_name,
            customer_email,
            product_id,
            product_name,
            quantity,
            unit_price,
            line_total,
            order_total,
            order_status,
            created_at,
        ) in crud_report.recent_order_details(session, limit=limit)
    ]
