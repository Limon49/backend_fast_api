"""Reusable FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends, Query
from sqlmodel import Session

from app.core.database import get_session


class Pagination:
    """``?limit=&offset=`` for every list endpoint.

    A dependency *class* keeps the two parameters out of every route signature
    while still showing them in ``/docs``.
    """

    def __init__(
        self,
        limit: int = Query(default=50, ge=1, le=200, description="Rows to return"),
        offset: int = Query(default=0, ge=0, description="Rows to skip"),
    ) -> None:
        self.limit = limit
        self.offset = offset


#: A database session for the current request.
SessionDep = Annotated[Session, Depends(get_session)]

#: The parsed ``limit``/``offset`` query parameters.
PaginationDep = Annotated[Pagination, Depends(Pagination)]
