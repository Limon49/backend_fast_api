"""Aggregate queries behind the reports endpoints.

These are the queries you would otherwise type by hand in TablePlus; exposing
them keeps the API and the database answers in sync.
"""

from sqlmodel import Session, func, select

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User


def sales_by_product(session: Session) -> list[tuple]:
    """Units sold and revenue per product, best sellers first.

    Cancelled orders are excluded, so the numbers mean "money we kept".
    """
    statement = (
        select(
            Product.id,
            Product.name,
            func.coalesce(func.sum(OrderItem.quantity), 0),
            func.coalesce(func.sum(OrderItem.line_total), 0),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.status == OrderStatus.PAID.value)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.line_total).desc())
    )
    return list(session.exec(statement).all())


def recent_order_details(session: Session, *, limit: int) -> list[tuple]:
    """Flat rows for the "recent purchases" table, newest first.

    Same columns as the ``order_details`` SQL view.
    """
    statement = (
        select(
            OrderItem.id,
            Order.id,
            User.name,
            User.email,
            Product.id,
            Product.name,
            OrderItem.quantity,
            OrderItem.unit_price,
            OrderItem.line_total,
            Order.total_amount,
            Order.status,
            Order.created_at,
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, Product.id == OrderItem.product_id)
        .join(User, User.id == Order.user_id)
        .order_by(Order.created_at.desc(), Order.id.desc(), OrderItem.id)
        .limit(limit)
    )
    return list(session.exec(statement).all())
