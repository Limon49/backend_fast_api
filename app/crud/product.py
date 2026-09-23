"""Product queries."""

from sqlmodel import Session, func, select

from app.core.exceptions import NotFoundError
from app.core.utils import utcnow
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def create_product(session: Session, data: ProductCreate) -> Product:
    """Insert a product and return it with its new ``id``."""
    product = Product.model_validate(data)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def list_products(
    session: Session,
    *,
    search: str | None = None,
    in_stock: bool | None = None,
    include_inactive: bool = False,
    limit: int,
    offset: int,
) -> tuple[list[Product], int]:
    """Return one page of products plus the total that matches the filters.

    - ``search``          part of the name, case-insensitive
    - ``in_stock``        True → only products with stock, False → only empty
    - ``include_inactive`` also show products that were soft-deleted
    """
    filters = []
    if not include_inactive:
        filters.append(Product.is_active == True)  # noqa: E712 (SQL, not Python)
    if search:
        filters.append(Product.name.ilike(f"%{search}%"))
    if in_stock is not None:
        filters.append(Product.stock > 0 if in_stock else Product.stock == 0)

    count_statement = select(func.count()).select_from(Product)
    statement = select(Product)
    for condition in filters:
        count_statement = count_statement.where(condition)
        statement = statement.where(condition)

    total = session.exec(count_statement).one()
    products = session.exec(
        statement.order_by(Product.name).offset(offset).limit(limit)
    ).all()
    return list(products), total


def get_product(session: Session, product_id: int) -> Product:
    """Fetch one product or raise :class:`NotFoundError`."""
    product = session.get(Product, product_id)
    if product is None:
        raise NotFoundError(f"Product {product_id} not found")
    return product


def update_product(session: Session, product: Product, data: ProductUpdate) -> Product:
    """Apply only the fields the client actually sent."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    product.updated_at = utcnow()
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def deactivate_product(session: Session, product: Product) -> Product:
    """Soft delete.

    A real ``DELETE`` would either fail (order lines reference this product) or
    erase history. Flipping ``is_active`` keeps old receipts readable while
    hiding the product from the shop.
    """
    product.is_active = False
    product.updated_at = utcnow()
    session.add(product)
    session.commit()
    session.refresh(product)
    return product
