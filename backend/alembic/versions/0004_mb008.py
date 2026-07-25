"""MB-008 masjid registration, soft-delete, audit log

Add deleted_at + timezone to masjids; add masjid_operator_roles join table;
add masjid_audit_logs table (no FK to masjids — audit rows survive deletion).

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("masjids", sa.Column("timezone", sa.String(100), nullable=True))
    op.add_column("masjids", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_masjids_deleted_at", "masjids", ["deleted_at"])

    op.create_table(
        "masjid_operator_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("masjid_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["masjid_id"], ["masjids.id"]),
        sa.ForeignKeyConstraint(["operator_id"], ["operator_accounts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("masjid_id", "operator_id", name="uq_masjid_operator_role"),
    )

    op.create_table(
        "masjid_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_operator_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("masjid_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("old_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_values", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("masjid_audit_logs")
    op.drop_table("masjid_operator_roles")
    op.drop_index("ix_masjids_deleted_at", table_name="masjids")
    op.drop_column("masjids", "deleted_at")
    op.drop_column("masjids", "timezone")
