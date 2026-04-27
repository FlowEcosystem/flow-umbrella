"""enrollment_token_max_uses

Revision ID: j7k8l9m0n1o2
Revises: i6j7k8l9m0n1
Create Date: 2026-04-27 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "j7k8l9m0n1o2"
down_revision: str | None = "i6j7k8l9m0n1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "enrollment_tokens",
        sa.Column("max_uses", sa.Integer(), nullable=True),
    )
    op.add_column(
        "enrollment_tokens",
        sa.Column("uses_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("enrollment_tokens", "uses_count")
    op.drop_column("enrollment_tokens", "max_uses")
