"""add services and refactor policy rules

Revision ID: b7c8d9e0f1a2
Revises: a3f1c2d4e5b6
Create Date: 2026-04-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = 'a3f1c2d4e5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Переименовываем policies.rules → policies.custom_rules
    op.alter_column('policies', 'rules', new_column_name='custom_rules')

    # 2. Таблица services (переиспользует уже существующий тип policysource)
    op.create_table(
        'services',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source', postgresql.ENUM('local', 'global', name='policysource', create_type=False), nullable=False, server_default='local'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('rules', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_services')),
    )
    op.create_index('ix_services_category', 'services', ['category'], unique=False)
    op.create_index('ix_services_source', 'services', ['source'], unique=False)

    # 3. Join-таблица policy_services
    op.create_table(
        'policy_services',
        sa.Column('policy_id', sa.Uuid(), nullable=False),
        sa.Column('service_id', sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], name=op.f('fk_policy_services_policy_id_policies'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], name=op.f('fk_policy_services_service_id_services'), ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('policy_id', 'service_id', name=op.f('pk_policy_services')),
    )


def downgrade() -> None:
    op.drop_table('policy_services')
    op.drop_index('ix_services_source', table_name='services')
    op.drop_index('ix_services_category', table_name='services')
    op.drop_table('services')
    op.alter_column('policies', 'custom_rules', new_column_name='rules')
