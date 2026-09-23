"""
SQLModel *table* models — the database truth.

Everything that is a real table lives in this package and is re-exported here,
so ``import app.models`` registers all tables with SQLModel's metadata. Both
``create_all`` and Alembic autogenerate rely on that.

Relationship map::

    user ──< orders ──< order_item >── product

    user       who buys
    orders     one purchase by one user
    order_item one line of that purchase (how many, at what price)
    product    what can be bought
"""

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User

__all__ = ["Order", "OrderItem", "OrderStatus", "Product", "User"]
