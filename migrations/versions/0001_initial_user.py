"""initial user table (baseline)

This migration records the schema this project started with: a single ``user``
table that already exists in the local ``aiquest_db`` database.

Because that table is already there, the first migration on such a database is
"stamped" as applied instead of being run::

    uv run alembic stamp 0001_initial_user
    uv run alembic upgrade head

On a brand new database you just run ``alembic upgrade head`` and this creates
``user`` for you.

Revision ID: 0001_initial_user
Revises:
Create Date: 2026-09-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_initial_user"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
    op.create_index(op.f("ix_user_name"), "user", ["name"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_name"), table_name="user")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
