"""initial schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-06-30

"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "masjids",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address_line", sa.String(500), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("country", sa.String(2), nullable=False, server_default="US"),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("calculation_method", sa.String(50), nullable=False, server_default="ISNA"),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_masjids_name", "masjids", ["name"])
    op.create_index("ix_masjids_city", "masjids", ["city"])

    op.create_table(
        "operator_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("masjid_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["masjid_id"], ["masjids.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="uq_operator_username"),
    )

    op.create_table(
        "iqamah_times",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("masjid_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prayer", sa.String(20), nullable=False),
        sa.Column("minutes_after_adhan", sa.Integer(), nullable=True),
        sa.Column("fixed_time", sa.Time(), nullable=True),
        sa.ForeignKeyConstraint(["masjid_id"], ["masjids.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("masjid_id", "prayer", name="uq_iqamah_masjid_prayer"),
    )

    op.create_table(
        "jumuah_times",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("masjid_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(255), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("time", sa.Time(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["masjid_id"], ["masjids.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jumuah_masjid_order", "jumuah_times", ["masjid_id", "sort_order"])

    op.create_table(
        "khutbah_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("masjid_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="live"),
        sa.ForeignKeyConstraint(["masjid_id"], ["masjids.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_khutbah_sessions_masjid_status", "khutbah_sessions", ["masjid_id", "status"]
    )

    op.create_table(
        "khutbah_segments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("arabic_text", sa.Text(), nullable=False),
        sa.Column("english_text", sa.Text(), nullable=True),
        sa.Column("segment_type", sa.String(20), nullable=False, server_default="plain_speech"),
        sa.Column("quran_surah", sa.Integer(), nullable=True),
        sa.Column("quran_ayah", sa.Integer(), nullable=True),
        sa.Column("is_partial", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["session_id"], ["khutbah_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_khutbah_segments_session_seq",
        "khutbah_segments",
        ["session_id", "sequence_number"],
    )


def downgrade() -> None:
    op.drop_table("khutbah_segments")
    op.drop_table("khutbah_sessions")
    op.drop_table("jumuah_times")
    op.drop_table("iqamah_times")
    op.drop_table("operator_accounts")
    op.drop_table("masjids")
