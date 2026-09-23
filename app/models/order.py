"""
The purchase tables — "who bought what, at what price".

``orders`` is one purchase, ``order_item`` is one line inside it::

    user ──< orders ──< order_item >── product

Three deliberate choices worth remembering:

1. The table is called **``orders``**, not ``order``. ``ORDER`` is a reserved
   word in MySQL, so every raw query would need backticks (``SELECT * FROM
   `order` ``). Not worth the pain.
2. **``unit_price`` and ``line_total`` are copies** taken at purchase time. If
   you edit a product's price tomorrow, yesterday's receipts stay correct —
   that is exactly how real shops work.
3. **Deleting is soft** for products (``is_active=False``) because order lines
   point at them. Hard deletes would break historical orders.
"""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

from app.core.utils import utcnow
from app.models.product import Product
from app.models.user import User


class OrderStatus(StrEnum):
    """The only allowed values for ``orders.status``.

    Because it is a ``StrEnum``, ``OrderStatus.PAID == "paid"`` is true, so it
    works directly both in the database and in JSON.
    """

    PAID = "paid"
    CANCELLED = "cancelled"


class Order(SQLModel, table=True):
    """One purchase made by one user."""

    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_orders_total_not_negative"),
    )

    id: int | None = Field(default=None, primary_key=True)

    #: ``ondelete="RESTRICT"``: a user with orders cannot simply vanish, which
    #: keeps purchase history honest.
    user_id: int = Field(foreign_key="user.id", index=True, ondelete="RESTRICT")

    status: str = Field(default=OrderStatus.PAID.value, index=True, max_length=20)

    #: Sum of the line totals, computed by the server from the current prices.
    total_amount: Decimal = Field(
        default=Decimal("0.00"), sa_column=Column(Numeric(10, 2), nullable=False)
    )
    created_at: datetime = Field(default_factory=utcnow, index=True)

    user: User | None = Relationship(back_populates="orders")

    #: ``lazy="selectin"`` loads the lines up front (one extra query), so
    #: serialising an order never triggers a surprise query — or blows up
    #: because the session already closed.
    items: list["OrderItem"] = Relationship(
        back_populates="order",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )


class OrderItem(SQLModel, table=True):
    """One line of an order: how many of which product, at which price."""

    __tablename__ = "order_item"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_item_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_order_item_unit_price_not_negative"),
    )

    id: int | None = Field(default=None, primary_key=True)

    #: Deleting an order removes its lines (CASCADE); a product cannot be
    #: hard-deleted while it appears on a receipt (RESTRICT).
    order_id: int = Field(foreign_key="orders.id", index=True, ondelete="CASCADE")
    product_id: int = Field(foreign_key="product.id", index=True, ondelete="RESTRICT")

    quantity: int = Field(ge=1)
    unit_price: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    line_total: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))

    order: Order | None = Relationship(back_populates="items")
    product: Product | None = Relationship(sa_relationship_kwargs={"lazy": "selectin"})
