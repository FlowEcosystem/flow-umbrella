"""add agent token fields and commands table

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-04-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd2e3f4a5b6c7'
down_revision: Union[str, Sequence[str], None] = 'c1d2e3f4a5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Agent: поля после enrollment ---
    op.add_column('agents', sa.Column('agent_token_hash', sa.String(64), nullable=True))
    op.add_column('agents', sa.Column('cert_serial', sa.String(64), nullable=True))
    op.add_column('agents', sa.Column('cert_expires_at', sa.DateTime(timezone=True), nullable=True))

    op.create_index('ix_agents_agent_token_hash', 'agents', ['agent_token_hash'])

    # --- Commands ---
    # asyncpg не поддерживает несколько команд в одном execute — каждый statement отдельно.
    op.execute("DROP TYPE IF EXISTS command_type CASCADE")
    op.execute("DROP TYPE IF EXISTS command_status CASCADE")
    op.execute("CREATE TYPE command_type AS ENUM ('reboot', 'collect_diagnostics', 'update_self', 'apply_config')")
    op.execute("CREATE TYPE command_status AS ENUM ('pending', 'sent', 'acknowledged', 'success', 'failure', 'timeout')")
    op.execute("""
        CREATE TABLE commands (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            agent_id        UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
            type            command_type NOT NULL,
            status          command_status NOT NULL DEFAULT 'pending',
            payload         JSON,
            result          JSON,
            error_message   VARCHAR(1024),
            issued_by_id    UUID REFERENCES admins(id) ON DELETE SET NULL,
            sent_at         TIMESTAMPTZ,
            acknowledged_at TIMESTAMPTZ,
            completed_at    TIMESTAMPTZ,
            expires_at      TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX ix_commands_agent_id ON commands (agent_id)")
    op.execute("CREATE INDEX ix_commands_status   ON commands (status)")


def downgrade() -> None:
    op.drop_index('ix_commands_status', table_name='commands')
    op.drop_index('ix_commands_agent_id', table_name='commands')
    op.drop_table('commands')
    op.execute('DROP TYPE command_status')
    op.execute('DROP TYPE command_type')

    op.drop_index('ix_agents_agent_token_hash', table_name='agents')
    op.drop_column('agents', 'cert_expires_at')
    op.drop_column('agents', 'cert_serial')
    op.drop_column('agents', 'agent_token_hash')
