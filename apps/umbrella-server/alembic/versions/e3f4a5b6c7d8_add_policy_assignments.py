"""add policy assignments

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-04-24 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e3f4a5b6c7d8'
down_revision: Union[str, Sequence[str], None] = 'd2e3f4a5b6c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('policies', sa.Column('is_global', sa.Boolean(), nullable=False, server_default='false'))

    op.execute("""
        CREATE TABLE policy_group_assignments (
            policy_id       UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
            group_id        UUID NOT NULL REFERENCES groups(id)   ON DELETE CASCADE,
            assigned_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            assigned_by_id  UUID REFERENCES admins(id) ON DELETE SET NULL,
            PRIMARY KEY (policy_id, group_id)
        )
    """)
    op.execute("CREATE INDEX ix_pga_group_id ON policy_group_assignments (group_id)")

    op.execute("""
        CREATE TABLE policy_agent_assignments (
            policy_id       UUID NOT NULL REFERENCES policies(id) ON DELETE CASCADE,
            agent_id        UUID NOT NULL REFERENCES agents(id)   ON DELETE CASCADE,
            assigned_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
            assigned_by_id  UUID REFERENCES admins(id) ON DELETE SET NULL,
            PRIMARY KEY (policy_id, agent_id)
        )
    """)
    op.execute("CREATE INDEX ix_paa_agent_id ON policy_agent_assignments (agent_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_paa_agent_id")
    op.execute("DROP TABLE IF EXISTS policy_agent_assignments")
    op.execute("DROP INDEX IF EXISTS ix_pga_group_id")
    op.execute("DROP TABLE IF EXISTS policy_group_assignments")
    op.drop_column('policies', 'is_global')
