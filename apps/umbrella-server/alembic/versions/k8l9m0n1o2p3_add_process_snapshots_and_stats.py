"""add_process_snapshots_and_stats

Revision ID: k8l9m0n1o2p3
Revises: j7k8l9m0n1o2
Create Date: 2026-04-27 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "k8l9m0n1o2p3"
down_revision: str | None = "j7k8l9m0n1o2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_process_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processes", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.ForeignKeyConstraint(
            ["agent_id"], ["agents.id"],
            name=op.f("fk_agent_process_snapshots_agent_id_agents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_process_snapshots")),
    )
    op.create_index(
        op.f("ix_agent_process_snapshots_agent_collected"),
        "agent_process_snapshots",
        ["agent_id", "collected_at"],
    )

    op.create_table(
        "agent_process_stats",
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("process_name", sa.String(255), nullable=False),
        sa.Column("seen_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["agent_id"], ["agents.id"],
            name=op.f("fk_agent_process_stats_agent_id_agents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "agent_id", "process_name", name=op.f("pk_agent_process_stats")
        ),
    )
    op.create_index(
        op.f("ix_agent_process_stats_agent_count"),
        "agent_process_stats",
        ["agent_id", "seen_count"],
    )

    # Add kill_process to command_type enum
    op.execute("ALTER TYPE command_type ADD VALUE IF NOT EXISTS 'kill_process'")


def downgrade() -> None:
    op.drop_index(
        op.f("ix_agent_process_stats_agent_count"), table_name="agent_process_stats"
    )
    op.drop_table("agent_process_stats")
    op.drop_index(
        op.f("ix_agent_process_snapshots_agent_collected"),
        table_name="agent_process_snapshots",
    )
    op.drop_table("agent_process_snapshots")
    # Note: PostgreSQL does not support removing enum values; kill_process stays.
