"""User queries."""

from sqlmodel import Session, func, select

from app.core.exceptions import ConflictError, NotFoundError
from app.models.user import User
from app.schemas.user import UserCreate


def create_user(session: Session, data: UserCreate) -> User:
    """Insert a user and return it with its new ``id``.

    ``email`` is unique in the database, so a duplicate would blow up as a 500
    error. Catching ``IntegrityError`` and turning it into a 409 says exactly
    what went wrong.
    """
    from sqlalchemy.exc import IntegrityError

    user = User.model_validate(data)
    session.add(user)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError(f"A user with email '{data.email}' already exists") from exc
    session.refresh(user)
    return user


def list_users(session: Session, *, limit: int, offset: int) -> tuple[list[User], int]:
    """Return one page of users plus the total number of users."""
    total = session.exec(select(func.count()).select_from(User)).one()
    users = session.exec(select(User).order_by(User.id).offset(offset).limit(limit)).all()
    return list(users), total


def get_user(session: Session, user_id: int) -> User:
    """Fetch one user or raise :class:`NotFoundError`."""
    user = session.get(User, user_id)
    if user is None:
        raise NotFoundError(f"User {user_id} not found")
    return user
