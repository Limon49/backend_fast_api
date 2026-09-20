"""
User models for the learning project.

We split the User into three related models — a common SQLModel pattern:

  - UserBase:   fields shared by all variants (avoids repetition)
  - User:       the actual DATABASE TABLE model (table=True)
  - UserCreate: what the CLIENT sends us in a POST request (no id)
  - UserRead:   what we SEND BACK to the client (includes id, hides
                anything sensitive if you add fields like a password later)
"""

from sqlmodel import SQLModel, Field
from typing import Optional


class UserBase(SQLModel):
    name: str = Field(index=True)
    email: str = Field(index=True, unique=True)
    age: Optional[int] = None


class User(UserBase, table=True):
    """The actual database table."""
    id: Optional[int] = Field(default=None, primary_key=True)


class UserCreate(UserBase):
    """Schema for creating a user (request body for POST /users)."""
    pass


class UserRead(UserBase):
    """Schema for reading a user (response body for GET endpoints)."""
    id: int
