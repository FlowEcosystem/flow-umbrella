"""enrollment_tokens table, rework agent lifecycle

Revision ID: i6j7k8l9m0n1
Revises: h5i6j7k8l9m0
Create Date: 2026-04-26 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'i6j7k8l9m0n1'
down_revision: Union[str, Sequence[str], None] = 'h5i6j7k8l9m0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Новая таблица enrollment_tokens
    op.create_table(
        "enrollment_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.String(255), nullable=True),
        sa.Column("group_id", sa.Uuid(), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("used_by_agent_id", sa.Uuid(), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="SET NULL",
                                name="fk_enrollment_tokens_group_id_groups"),
        sa.ForeignKeyConstraint(["used_by_agent_id"], ["agents.id"], ondelete="SET NULL",
                                name="fk_enrollment_tokens_used_by_agent_id_agents"),
        sa.ForeignKeyConstraint(["created_by_id"], ["admins.id"], ondelete="SET NULL",
                                name="fk_enrollment_tokens_created_by_id_admins"),
        sa.PrimaryKeyConstraint("id", name="pk_enrollment_tokens"),
        sa.UniqueConstraint("token_hash", name="uq_enrollment_tokens_token_hash"),
    )
    op.create_index("ix_enrollment_tokens_token_hash", "enrollment_tokens", ["token_hash"])

    # 2. agents: убираем enrollment_token_*, делаем hostname и os nullable,
    #    убираем hostname unique index (агенты больше не создаются вручную с заданным hostname)
    op.drop_index("uq_agents_hostname_active", table_name="agents")
    op.drop_index("ix_agents_enrollment_token_hash", table_name="agents")
    op.drop_column("agents", "enrollment_token_hash")
    op.drop_column("agents", "enrollment_token_expires_at")
    op.alter_column("agents", "hostname", nullable=True)
    op.alter_column("agents", "os", nullable=True)

    # 3. Убираем статус pending из enum (агенты теперь сразу active после enrollment)
    #    PostgreSQL не позволяет удалять значения enum — оставляем его в типе,
    #    но больше не используем. Существующие pending-агенты → decommissioned.
    op.execute(
        "UPDATE agents SET status = 'decommissioned' WHERE status = 'pending' AND deleted_at IS NULL"
    )


def downgrade() -> None:
    op.add_column("agents", sa.Column("enrollment_token_expires_at",
                                      sa.DateTime(timezone=True), nullable=True))
    op.add_column("agents", sa.Column("enrollment_token_hash",
                                      sa.String(64), nullable=True))
    op.create_index("ix_agents_enrollment_token_hash", "agents", ["enrollment_token_hash"])
    op.alter_column("agents", "hostname", nullable=False,
                    server_default="unknown")
    op.alter_column("agents", "os", nullable=False)
    op.drop_index("ix_enrollment_tokens_token_hash", table_name="enrollment_tokens")
    op.drop_table("enrollment_tokens")
