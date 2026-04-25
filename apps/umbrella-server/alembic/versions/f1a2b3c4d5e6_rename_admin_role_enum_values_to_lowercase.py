"""rename admin_role enum values to lowercase

Revision ID: f1a2b3c4d5e6
Revises: e3f4a5b6c7d8
Create Date: 2026-04-24 20:10:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = 'e3f4a5b6c7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE admin_role RENAME VALUE 'SUPERADMIN' TO 'superadmin'")
    op.execute("ALTER TYPE admin_role RENAME VALUE 'ADMIN' TO 'admin'")
    op.execute("ALTER TYPE admin_role RENAME VALUE 'VIEWER' TO 'viewer'")


def downgrade() -> None:
    op.execute("ALTER TYPE admin_role RENAME VALUE 'superadmin' TO 'SUPERADMIN'")
    op.execute("ALTER TYPE admin_role RENAME VALUE 'admin' TO 'ADMIN'")
    op.execute("ALTER TYPE admin_role RENAME VALUE 'viewer' TO 'VIEWER'")
