"""products and orders

Adds the shopping feature: three tables so a user can buy products and every
purchase is stored.

* ``product``    what can be bought
* ``orders``     one purchase by one user (a *reserved word* in MySQL, hence the
                 plural table name)
* ``order_item`` one line per purchase: how many of which product, at the price
                 that was valid at that moment

Revision ID: 0002_products_and_orders
Revises: 0001_initial_user
Create Date: 2026-09-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_products_and_orders"
down_revision: Union[str, None] = "0001_initial_user"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "product",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("price > 0", name="ck_product_price_positive"),
        sa.CheckConstraint("stock >= 0", name="ck_product_stock_not_negative"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_product_name"), "product", ["name"], unique=False)
    op.create_index(op.f("ix_product_is_active"), "product", ["is_active"], unique=False)

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("total_amount >= 0", name="ck_orders_total_not_negative"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            name="fk_orders_user_id_user",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_orders_user_id"), "orders", ["user_id"], unique=False)
    op.create_index(op.f("ix_orders_status"), "orders", ["status"], unique=False)
    op.create_index(op.f("ix_orders_created_at"), "orders", ["created_at"], unique=False)

    op.create_table(
        "order_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("line_total", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_order_item_quantity_positive"),
        sa.CheckConstraint(
            "unit_price >= 0", name="ck_order_item_unit_price_not_negative"
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name="fk_order_item_order_id_orders",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["product.id"],
            name="fk_order_item_product_id_product",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_item_order_id"), "order_item", ["order_id"], unique=False)
    op.create_index(
        op.f("ix_order_item_product_id"), "order_item", ["product_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_order_item_product_id"), table_name="order_item")
    op.drop_index(op.f("ix_order_item_order_id"), table_name="order_item")
    op.drop_table("order_item")

    op.drop_index(op.f("ix_orders_created_at"), table_name="orders")
    op.drop_index(op.f("ix_orders_status"), table_name="orders")
    op.drop_index(op.f("ix_orders_user_id"), table_name="orders")
    op.drop_table("orders")

    op.drop_index(op.f("ix_product_is_active"), table_name="product")
    op.drop_index(op.f("ix_product_name"), table_name="product")
    op.drop_table("product")
