"""MB-009: masjid moderation_status column

Add moderation_status VARCHAR(20) NOT NULL DEFAULT 'pending' to masjids,
constrained to ('pending', 'approved', 'rejected') via a CHECK constraint,
and indexed for efficient admin queries.

Existing rows are backfilled to 'approved' so that previously live masjids
remain publicly visible after this migration runs.  New registrations default
to 'pending' and require an admin to approve before appearing publicly.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-08-01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add with a nullable=True first so we can backfill before adding the NOT NULL constraint.
    op.add_column(
        "masjids",
        sa.Column(
            "moderation_status",
            sa.String(20),
            nullable=True,
            server_default="pending",
        ),
    )

    # Backfill all existing rows to 'approved' — they were live before moderation existed.
    op.execute("UPDATE masjids SET moderation_status = 'approved' WHERE moderation_status IS NULL")

    # Now tighten to NOT NULL.
    op.alter_column("masjids", "moderation_status", nullable=False)

    op.create_check_constraint(
        "ck_masjids_moderation_status",
        "masjids",
        "moderation_status IN ('pending', 'approved', 'rejected')",
    )
    op.create_index("ix_masjids_moderation_status", "masjids", ["moderation_status"])


def downgrade() -> None:
    op.drop_index("ix_masjids_moderation_status", table_name="masjids")
    op.drop_constraint("ck_masjids_moderation_status", "masjids", type_="check")
    op.drop_column("masjids", "moderation_status")
