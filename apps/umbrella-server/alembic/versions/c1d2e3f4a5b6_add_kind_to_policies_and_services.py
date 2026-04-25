"""add kind to policies and services

Revision ID: c1d2e3f4a5b6
Revises: b7c8d9e0f1a2
Create Date: 2026-04-23 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE policykind AS ENUM ('traffic', 'process')")

    op.add_column('policies', sa.Column(
        'kind',
        sa.Enum('traffic', 'process', name='policykind', create_constraint=False),
        nullable=False,
        server_default='traffic',
    ))
    op.add_column('services', sa.Column(
        'kind',
        sa.Enum('traffic', 'process', name='policykind', create_constraint=False),
        nullable=False,
        server_default='traffic',
    ))

    op.create_index('ix_policies_kind', 'policies', ['kind'])
    op.create_index('ix_services_kind',  'services',  ['kind'])


def downgrade() -> None:
    op.drop_index('ix_services_kind',  table_name='services')
    op.drop_index('ix_policies_kind', table_name='policies')
    op.drop_column('services',  'kind')
    op.drop_column('policies', 'kind')
    op.execute('DROP TYPE policykind')
