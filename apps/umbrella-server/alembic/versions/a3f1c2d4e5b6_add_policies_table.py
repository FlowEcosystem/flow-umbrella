"""add policies table

Revision ID: a3f1c2d4e5b6
Revises: bb6189232cb8
Create Date: 2026-04-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a3f1c2d4e5b6'
down_revision: Union[str, Sequence[str], None] = 'bb6189232cb8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE policysource AS ENUM ('local', 'global')")
    op.execute("CREATE TYPE policyaction AS ENUM ('block', 'allow')")

    op.create_table(
        'policies',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source', postgresql.ENUM('local', 'global', name='policysource', create_type=False), nullable=False, server_default='local'),
        sa.Column('action', postgresql.ENUM('block', 'allow', name='policyaction', create_type=False), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('rules', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('overridable', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('hq_policy_id', sa.Uuid(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_policies')),
    )
    op.create_index('ix_policies_source', 'policies', ['source'], unique=False)
    op.create_index('ix_policies_is_active', 'policies', ['is_active'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_policies_is_active', table_name='policies')
    op.drop_index('ix_policies_source', table_name='policies')
    op.drop_table('policies')
    op.execute("DROP TYPE IF EXISTS policyaction")
    op.execute("DROP TYPE IF EXISTS policysource")
