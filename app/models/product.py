"""The ``product`` table: the things a user can buy."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Column, Numeric, Text
from sqlmodel import Field, SQLModel

from app.core.utils import utcnow


class ProductBase(SQLModel):
    """Fields shared by every product shape."""

    name: str = Field(index=True, max_length=120)
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    #: DECIMAL(10,2) instead of FLOAT: money must never lose cents to rounding.
    price: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))

    stock: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True, index=True)


class Product(ProductBase, table=True):
    """The actual database table."""

    __tablename__ = "product"
    __table_args__ = (
        # The database refuses nonsense even if some future code forgets to
        # validate it. Cheap insurance, and it shows up in TablePlus.
        CheckConstraint("price > 0", name="ck_product_price_positive"),
        CheckConstraint("stock >= 0", name="ck_product_stock_not_negative"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
