"""add agent_metrics table

Revision ID: h5i6j7k8l9m0
Revises: g4h5i6j7k8l9
Create Date: 2026-04-26 13:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'h5i6j7k8l9m0'
down_revision: Union[str, Sequence[str], None] = 'g4h5i6j7k8l9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_metrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", sa.Uuid(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cpu_percent", sa.Float(), nullable=True),
        sa.Column("ram_used_mb", sa.Integer(), nullable=True),
        sa.Column("ram_total_mb", sa.Integer(), nullable=True),
        sa.Column("disk_used_gb", sa.Float(), nullable=True),
        sa.Column("disk_total_gb", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE",
                                name="fk_agent_metrics_agent_id_agents"),
        sa.PrimaryKeyConstraint("id", name="pk_agent_metrics"),
    )
    op.create_index("ix_agent_metrics_agent_collected", "agent_metrics",
                    ["agent_id", "collected_at"])


def downgrade() -> None:
    op.drop_index("ix_agent_metrics_agent_collected", table_name="agent_metrics")
    op.drop_table("agent_metrics")
