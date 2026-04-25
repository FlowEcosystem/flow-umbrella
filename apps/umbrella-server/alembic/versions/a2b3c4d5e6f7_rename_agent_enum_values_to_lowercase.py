"""rename agent_status and agent_os enum values to lowercase

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-04-24 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, Sequence[str], None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE agent_status RENAME VALUE 'PENDING' TO 'pending'")
    op.execute("ALTER TYPE agent_status RENAME VALUE 'ACTIVE' TO 'active'")
    op.execute("ALTER TYPE agent_status RENAME VALUE 'DISABLED' TO 'disabled'")
    op.execute("ALTER TYPE agent_status RENAME VALUE 'DECOMMISSIONED' TO 'decommissioned'")

    op.execute("ALTER TYPE agent_os RENAME VALUE 'WINDOWS' TO 'windows'")
    op.execute("ALTER TYPE agent_os RENAME VALUE 'LINUX' TO 'linux'")
    op.execute("ALTER TYPE agent_os RENAME VALUE 'MACOS' TO 'macos'")


def downgrade() -> None:
    op.execute("ALTER TYPE agent_status RENAME VALUE 'pending' TO 'PENDING'")
    op.execute("ALTER TYPE agent_status RENAME VALUE 'active' TO 'ACTIVE'")
    op.execute("ALTER TYPE agent_status RENAME VALUE 'disabled' TO 'DISABLED'")
    op.execute("ALTER TYPE agent_status RENAME VALUE 'decommissioned' TO 'DECOMMISSIONED'")

    op.execute("ALTER TYPE agent_os RENAME VALUE 'windows' TO 'WINDOWS'")
    op.execute("ALTER TYPE agent_os RENAME VALUE 'linux' TO 'LINUX'")
    op.execute("ALTER TYPE agent_os RENAME VALUE 'macos' TO 'MACOS'")
