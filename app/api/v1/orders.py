"""Order endpoints — buying things, and looking up what was bought."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import PaginationDep, SessionDep
from app.crud import order as crud_order
from app.models.order import OrderStatus
from app.schemas.order import OrderCreate, OrderList, OrderRead

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "",
    response_model=OrderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Buy products (creates a paid order)",
    responses={
        404: {"description": "Unknown user or product"},
        409: {"description": "Product inactive, or not enough stock"},
        422: {"description": "Body failed validation (e.g. quantity 0)"},
    },
)
def create_order(payload: OrderCreate, session: SessionDep) -> OrderRead:
    """The main event: one request = one purchase.

    Send the user and the lines you want::

        {"user_id": 1, "items": [{"product_id": 1, "quantity": 2}]}

    The server checks the user, the products, their availability and the stock,
    takes the prices **from the database**, decreases the stock, and saves the
    order with its lines — all in one transaction, so it either all happens or
    nothing does.
    """
    return OrderRead.from_model(crud_order.create_order(session, payload))


@router.get("", response_model=OrderList, summary="List orders")
def list_orders(
    session: SessionDep,
    page: PaginationDep,
    user_id: Annotated[int | None, Query(description="Only orders of this user")] = None,
    status_filter: Annotated[
        OrderStatus | None, Query(alias="status", description="paid or cancelled")
    ] = None,
) -> OrderList:
    orders, total = crud_order.list_orders(
        session,
        user_id=user_id,
        status=status_filter.value if status_filter else None,
        limit=page.limit,
        offset=page.offset,
    )
    return OrderList(
        items=[OrderRead.from_model(order) for order in orders],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{order_id}", response_model=OrderRead, summary="Get one order")
def get_order(order_id: int, session: SessionDep) -> OrderRead:
    return OrderRead.from_model(crud_order.get_order(session, order_id))


@router.post(
    "/{order_id}/cancel",
    response_model=OrderRead,
    summary="Cancel an order and return the stock",
)
def cancel_order(order_id: int, session: SessionDep) -> OrderRead:
    """Mark an order cancelled and put every product back on the shelf.

    Calling this twice is a 409, not a double restock.
    """
    return OrderRead.from_model(crud_order.cancel_order(session, order_id))
