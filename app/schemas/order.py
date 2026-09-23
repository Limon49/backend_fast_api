"""Order request/response contracts, and the ORM → schema mapper.

``OrderRead.from_model`` exists because the API shape differs slightly from the
database shape: an ``OrderItem`` row knows a ``product_id``, while the client
wants to see ``product_name``. Doing that mapping explicitly (instead of hiding
it in a config flag) keeps the output obvious and easy to test.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import Order, OrderStatus
from app.schemas.common import Money, Page
from app.schemas.product import ProductRead
from app.schemas.user import UserRead


class OrderItemCreate(BaseModel):
    """One line the client asks for: which product, how many."""

    product_id: int = Field(gt=0, examples=[1])
    quantity: int = Field(default=1, gt=0, le=1000, examples=[2])


class OrderCreate(BaseModel):
    """Request body for ``POST /api/v1/orders`` — the "buy this" request.

    The client sends **product ids and quantities only**. Prices are always
    read from the database, so nobody can buy a €1000 item for €1.
    """

    user_id: int = Field(gt=0, examples=[1])
    items: list[OrderItemCreate] = Field(
        min_length=1,
        examples=[[{"product_id": 1, "quantity": 2}, {"product_id": 3, "quantity": 1}]],
    )


class OrderItemRead(BaseModel):
    """One line of a saved order."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: Money
    line_total: Money
    product: ProductRead | None = None


class OrderRead(BaseModel):
    """A saved order with everything a human wants to see."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: OrderStatus
    total_amount: Money
    created_at: datetime
    item_count: int
    items: list[OrderItemRead]
    user: UserRead | None = None

    @classmethod
    def from_model(cls, order: Order) -> "OrderRead":
        """Convert an ORM ``Order`` (relationships loaded) into the API shape."""
        items = [
            OrderItemRead(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name if item.product else "(deleted product)",
                quantity=item.quantity,
                unit_price=item.unit_price,
                line_total=item.line_total,
                product=ProductRead.model_validate(item.product) if item.product else None,
            )
            for item in order.items
        ]
        return cls(
            id=order.id,
            user_id=order.user_id,
            status=OrderStatus(order.status),
            total_amount=order.total_amount,
            created_at=order.created_at,
            item_count=len(items),
            items=items,
            user=UserRead.model_validate(order.user) if order.user else None,
        )


class OrderList(Page):
    """Paginated list of orders."""

    items: list[OrderRead]
