"""add sync_policies and decommission command types

Revision ID: g4h5i6j7k8l9
Revises: a2b3c4d5e6f7
Create Date: 2026-04-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'g4h5i6j7k8l9'
down_revision: Union[str, Sequence[str], None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL allows adding enum values but not removing them.
    # IF NOT EXISTS guards against re-running on an already-migrated DB.
    op.execute("ALTER TYPE command_type ADD VALUE IF NOT EXISTS 'sync_policies'")
    op.execute("ALTER TYPE command_type ADD VALUE IF NOT EXISTS 'decommission'")


def downgrade() -> None:
    # Enum values cannot be removed in PostgreSQL without recreating the type.
    # Downgrade is intentionally a no-op — the values are harmless if unused.
    pass
