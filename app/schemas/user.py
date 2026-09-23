"""User request/response contracts."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import Page


class UserCreate(BaseModel):
    """Request body for ``POST /api/v1/users``."""

    name: str = Field(min_length=1, max_length=120, examples=["Limon"])
    email: EmailStr = Field(examples=["limon@edutune.com"])
    age: int | None = Field(default=None, ge=0, le=150, examples=[25])


class UserRead(BaseModel):
    """Response body for user endpoints.

    ``email`` is a plain ``str`` here (not ``EmailStr``) on purpose: rows that
    were inserted before this validation existed must not turn a GET into a
    500 error.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    age: int | None = None


class UserList(Page):
    """Paginated list of users."""

    items: list[UserRead]
