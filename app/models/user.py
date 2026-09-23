"""The ``user`` table: who buys things.

The table name stays ``user`` (singular) so the data that already exists in
``aiquest_db`` keeps working — see migration ``0001_initial_user``, which
records that existing table as the baseline of this project's schema.
"""

from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:  # imported only for type checkers, avoids a circular import
    from app.models.order import Order


class UserBase(SQLModel):
    """Fields shared by every user shape."""

    name: str = Field(index=True)
    email: str = Field(index=True, unique=True)
    age: Optional[int] = None


class User(UserBase, table=True):
    """The actual database table."""

    id: Optional[int] = Field(default=None, primary_key=True)

    #: Every order this user placed. Lazy by default: it is only loaded when
    #: something actually touches ``user.orders``.
    orders: list["Order"] = Relationship(back_populates="user")
