"""
Order logic — the "user buys products" transaction.

The whole purchase (order row + order lines + stock decrement) happens inside
**one database transaction**. If anything goes wrong halfway through, the
rollback leaves the database exactly as it was — you can never end up with a
half-saved order, or with stock taken away from a customer who paid nothing.

Order of business, all validated *before* anything is written:

1. the user exists                      → 404
2. every product exists                 → 404
3. every product is still on sale       → 409
4. there is enough stock for each line  → 409
5. prices are read from the database    → the client's price is never trusted
"""

from collections import defaultdict
from decimal import Decimal

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from sqlmodel import Session, func, select

from app.core.exceptions import ConflictError, NotFoundError
from app.core.utils import utcnow
from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User
from app.schemas.order import OrderCreate

CENTS = Decimal("0.01")


def create_order(session: Session, data: OrderCreate) -> Order:
    """Buy the requested products for the given user.

    Returns the saved order with its lines, the user, and the products loaded.
    """
    user = session.get(User, data.user_id)
    if user is None:
        raise NotFoundError(f"User {data.user_id} not found")

    # The same product may be listed twice in one request: merge the quantities
    # instead of creating two lines that each pass the stock check on their own.
    requested: dict[int, int] = defaultdict(int)
    for item in data.items:
        requested[item.product_id] += item.quantity

    # One query for every product, instead of one query per line.
    products = {
        product.id: product
        for product in session.exec(
            select(Product).where(Product.id.in_(list(requested)))
        ).all()
    }

    missing = sorted(set(requested) - set(products))
    if missing:
        raise NotFoundError(f"Product(s) not found: {missing}")

    for product_id, quantity in requested.items():
        product = products[product_id]
        if not product.is_active:
            raise ConflictError(f"Product '{product.name}' is not available for purchase")
        if product.stock < quantity:
            raise ConflictError(
                f"Not enough stock for '{product.name}' "
                f"(have {product.stock}, want {quantity})"
            )

    try:
        order = Order(
            user_id=user.id,
            status=OrderStatus.PAID.value,
            total_amount=Decimal("0.00"),
        )
        session.add(order)
        session.flush()  # sends the INSERT so the database assigns order.id

        total = Decimal("0.00")
        for product_id, quantity in requested.items():
            product = products[product_id]
            line_total = (product.price * quantity).quantize(CENTS)

            session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=product.price,  # snapshot of today's price
                    line_total=line_total,
                )
            )

            product.stock -= quantity
            product.updated_at = utcnow()
            session.add(product)

            total += line_total

        order.total_amount = total
        session.add(order)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise

    return get_order(session, order.id)


def _order_statement():
    """A base query that eagerly loads everything we serialise."""
    return select(Order).options(
        selectinload(Order.items).selectinload(OrderItem.product),
        selectinload(Order.user),
    )


def get_order(session: Session, order_id: int) -> Order:
    """Fetch one order or raise :class:`NotFoundError`."""
    order = session.exec(_order_statement().where(Order.id == order_id)).first()
    if order is None:
        raise NotFoundError(f"Order {order_id} not found")
    return order


def list_orders(
    session: Session,
    *,
    user_id: int | None = None,
    status: str | None = None,
    limit: int,
    offset: int,
) -> tuple[list[Order], int]:
    """Return one page of orders (newest first) plus the total that matches."""
    statement = _order_statement()
    count_statement = select(func.count()).select_from(Order)

    if user_id is not None:
        statement = statement.where(Order.user_id == user_id)
        count_statement = count_statement.where(Order.user_id == user_id)
    if status is not None:
        statement = statement.where(Order.status == status)
        count_statement = count_statement.where(Order.status == status)

    total = session.exec(count_statement).one()
    orders = session.exec(
        statement.order_by(Order.created_at.desc(), Order.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return list(orders), total


def cancel_order(session: Session, order_id: int) -> Order:
    """Cancel an order and put its products back on the shelf."""
    order = get_order(session, order_id)
    if order.status == OrderStatus.CANCELLED.value:
        raise ConflictError(f"Order {order_id} is already cancelled")

    try:
        for item in order.items:
            if item.product is not None:
                item.product.stock += item.quantity
                item.product.updated_at = utcnow()
                session.add(item.product)

        order.status = OrderStatus.CANCELLED.value
        session.add(order)
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise

    return get_order(session, order_id)
