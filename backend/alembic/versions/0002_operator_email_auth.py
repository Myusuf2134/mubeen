"""operator email auth

Rename operator_accounts.username → email, add is_admin and updated_at columns.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-22
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("uq_operator_username", "operator_accounts", type_="unique")
    op.alter_column("operator_accounts", "username", new_column_name="email")
    op.create_unique_constraint("uq_operator_email", "operator_accounts", ["email"])

    op.add_column(
        "operator_accounts",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "operator_accounts",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("operator_accounts", "updated_at")
    op.drop_column("operator_accounts", "is_admin")
    op.drop_constraint("uq_operator_email", "operator_accounts", type_="unique")
    op.alter_column("operator_accounts", "email", new_column_name="username")
    op.create_unique_constraint("uq_operator_username", "operator_accounts", ["username"])
