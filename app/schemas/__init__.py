"""
Request/response contracts.

Models in ``app/models`` describe what the *database* stores; schemas in this
package describe what the *API* accepts and returns. Keeping them apart means
you can add a `password` column later without leaking it in a response.

The pattern used everywhere is:

``XCreate``  what the client sends when creating an ``X``
``XUpdate``  what the client may change (every field optional)
``XRead``    what we send back
``XList``    the paginated listing envelope
"""

from app.schemas.common import Money, Page
from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderItemRead,
    OrderList,
    OrderRead,
)
from app.schemas.product import ProductCreate, ProductList, ProductRead, ProductUpdate
from app.schemas.report import OrderDetailRead, SalesReport, SalesRow
from app.schemas.user import UserCreate, UserList, UserRead

__all__ = [
    "Money",
    "OrderCreate",
    "OrderDetailRead",
    "OrderItemCreate",
    "OrderItemRead",
    "OrderList",
    "OrderRead",
    "Page",
    "ProductCreate",
    "ProductList",
    "ProductRead",
    "ProductUpdate",
    "SalesReport",
    "SalesRow",
    "UserCreate",
    "UserList",
    "UserRead",
]
