"""Shared schema helpers."""

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, PlainSerializer

#: Money is stored as DECIMAL(10,2) so it is exact, but Pydantic v2 renders
#: ``Decimal`` as a JSON *string* (``"19.99"``). This type keeps the storage
#: exact and the wire format a number, which reads much better in ``/docs``
#: and in a browser.
Money = Annotated[
    Decimal,
    PlainSerializer(float, return_type=float),
]


class Page(BaseModel):
    """Pagination metadata shared by every list response."""

    total: int
    limit: int
    offset: int
