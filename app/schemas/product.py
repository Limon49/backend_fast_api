"""Product request/response contracts."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Money, Page


class ProductCreate(BaseModel):
    """Request body for ``POST /api/v1/products``."""

    name: str = Field(min_length=1, max_length=120, examples=["FastAPI 101"])
    description: str | None = Field(default=None, examples=["Build your first API"])
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2, examples=[19.99])
    stock: int = Field(default=0, ge=0, examples=[25])
    is_active: bool = True


class ProductUpdate(BaseModel):
    """Request body for ``PATCH /api/v1/products/{id}``.

    Every field is optional: only the ones you send are changed
    (``model_dump(exclude_unset=True)`` in the CRUD layer).
    """

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductRead(BaseModel):
    """Response body for product endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    price: Money
    stock: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProductList(Page):
    """Paginated list of products."""

    items: list[ProductRead]
