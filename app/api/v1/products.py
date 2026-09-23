"""Product endpoints — the shop shelf."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import PaginationDep, SessionDep
from app.crud import product as crud_product
from app.schemas.product import ProductCreate, ProductList, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
)
def create_product(payload: ProductCreate, session: SessionDep) -> ProductRead:
    return ProductRead.model_validate(crud_product.create_product(session, payload))


@router.get("", response_model=ProductList, summary="List products")
def list_products(
    session: SessionDep,
    page: PaginationDep,
    search: Annotated[str | None, Query(description="Part of the product name")] = None,
    in_stock: Annotated[
        bool | None, Query(description="true = only in stock, false = only sold out")
    ] = None,
    include_inactive: Annotated[
        bool, Query(description="Also show products that were deactivated")
    ] = False,
) -> ProductList:
    """Browse the shelf: filter by name or availability, page through results."""
    products, total = crud_product.list_products(
        session,
        search=search,
        in_stock=in_stock,
        include_inactive=include_inactive,
        limit=page.limit,
        offset=page.offset,
    )
    return ProductList(
        items=[ProductRead.model_validate(product) for product in products],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{product_id}", response_model=ProductRead, summary="Get one product")
def get_product(product_id: int, session: SessionDep) -> ProductRead:
    return ProductRead.model_validate(crud_product.get_product(session, product_id))


@router.patch("/{product_id}", response_model=ProductRead, summary="Update a product")
def update_product(
    product_id: int, payload: ProductUpdate, session: SessionDep
) -> ProductRead:
    """Change price, stock or name. Only the fields you send are touched."""
    product = crud_product.get_product(session, product_id)
    return ProductRead.model_validate(crud_product.update_product(session, product, payload))


@router.delete(
    "/{product_id}",
    response_model=ProductRead,
    summary="Deactivate a product (soft delete)",
)
def delete_product(product_id: int, session: SessionDep) -> ProductRead:
    """Take a product off the shelf without touching past orders.

    Rows are never deleted: order lines point at products, so a hard delete
    would either fail or rewrite history. Set ``is_active=false`` instead, then
    put it back with ``PATCH {"is_active": true}`` if you change your mind.
    """
    product = crud_product.get_product(session, product_id)
    return ProductRead.model_validate(crud_product.deactivate_product(session, product))
