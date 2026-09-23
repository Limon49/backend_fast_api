"""User endpoints."""

from fastapi import APIRouter, status

from app.api.deps import PaginationDep, SessionDep
from app.crud import order as crud_order
from app.crud import user as crud_user
from app.schemas.order import OrderList, OrderRead
from app.schemas.user import UserCreate, UserList, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
)
def create_user(payload: UserCreate, session: SessionDep) -> UserRead:
    """Create a user and store it in the database (409 if the email is taken)."""
    return UserRead.model_validate(crud_user.create_user(session, payload))


@router.get("", response_model=UserList, summary="List users")
def list_users(session: SessionDep, page: PaginationDep) -> UserList:
    users, total = crud_user.list_users(session, limit=page.limit, offset=page.offset)
    return UserList(
        items=[UserRead.model_validate(user) for user in users],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{user_id}", response_model=UserRead, summary="Get one user")
def get_user(user_id: int, session: SessionDep) -> UserRead:
    return UserRead.model_validate(crud_user.get_user(session, user_id))


@router.get(
    "/{user_id}/orders",
    response_model=OrderList,
    summary="Purchase history for a user",
)
def list_user_orders(user_id: int, session: SessionDep, page: PaginationDep) -> OrderList:
    """Every order this user placed, newest first (404 if the user is unknown)."""
    crud_user.get_user(session, user_id)  # raises NotFoundError for unknown ids
    orders, total = crud_order.list_orders(
        session, user_id=user_id, limit=page.limit, offset=page.offset
    )
    return OrderList(
        items=[OrderRead.from_model(order) for order in orders],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )
