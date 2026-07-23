"""masjid_id nullable

Make operator_accounts.masjid_id optional so operators can be created
before being assigned to a masjid.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop the CASCADE FK so we can recreate it as SET NULL.
    op.drop_constraint(
        "operator_accounts_masjid_id_fkey", "operator_accounts", type_="foreignkey"
    )
    # Allow the column to be NULL.
    op.alter_column(
        "operator_accounts",
        "masjid_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    # Recreate FK with SET NULL so deleting a masjid leaves the operator intact.
    op.create_foreign_key(
        None,
        "operator_accounts",
        "masjids",
        ["masjid_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "operator_accounts_masjid_id_fkey", "operator_accounts", type_="foreignkey"
    )
    # Rows with NULL masjid_id cannot be restored — downgrade requires no such rows exist.
    op.alter_column(
        "operator_accounts",
        "masjid_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.create_foreign_key(
        None,
        "operator_accounts",
        "masjids",
        ["masjid_id"],
        ["id"],
        ondelete="CASCADE",
    )
