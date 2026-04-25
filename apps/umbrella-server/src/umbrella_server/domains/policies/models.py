"""Модели policies-домена."""

import enum
from uuid import UUID

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Table, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from umbrella_server.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class PolicyKind(str, enum.Enum):
    TRAFFIC = "traffic"
    PROCESS = "process"


class PolicySource(str, enum.Enum):
    LOCAL = "local"
    GLOBAL = "global"


class PolicyAction(str, enum.Enum):
    BLOCK = "block"
    ALLOW = "allow"


class PolicyRuleType(str, enum.Enum):
    DOMAIN = "domain"
    URL = "url"
    IP = "ip"
    PROCESS = "process"


policy_services = Table(
    "policy_services",
    Base.metadata,
    Column("policy_id", ForeignKey("policies.id", ondelete="CASCADE"), primary_key=True),
    Column("service_id", ForeignKey("services.id", ondelete="CASCADE"), primary_key=True),
)

policy_group_assignments = Table(
    "policy_group_assignments",
    Base.metadata,
    Column("policy_id",      ForeignKey("policies.id", ondelete="CASCADE"), primary_key=True),
    Column("group_id",       ForeignKey("groups.id",   ondelete="CASCADE"), primary_key=True),
    Column("assigned_at",    DateTime(timezone=True), nullable=False, server_default=text("now()")),
    Column("assigned_by_id", ForeignKey("admins.id",   ondelete="SET NULL"), nullable=True),
)

policy_agent_assignments = Table(
    "policy_agent_assignments",
    Base.metadata,
    Column("policy_id",      ForeignKey("policies.id", ondelete="CASCADE"), primary_key=True),
    Column("agent_id",       ForeignKey("agents.id",   ondelete="CASCADE"), primary_key=True),
    Column("assigned_at",    DateTime(timezone=True), nullable=False, server_default=text("now()")),
    Column("assigned_by_id", ForeignKey("admins.id",   ondelete="SET NULL"), nullable=True),
)


class Service(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "services"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    kind: Mapped[PolicyKind] = mapped_column(
        Enum(PolicyKind, name="policykind", create_constraint=False,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PolicyKind.TRAFFIC,
    )
    source: Mapped[PolicySource] = mapped_column(
        Enum(PolicySource, name="policysource", create_constraint=False,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PolicySource.LOCAL,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    rules: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))


class Policy(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "policies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    kind: Mapped[PolicyKind] = mapped_column(
        Enum(PolicyKind, name="policykind", create_constraint=False,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PolicyKind.TRAFFIC,
    )
    source: Mapped[PolicySource] = mapped_column(
        Enum(PolicySource, name="policysource", values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=PolicySource.LOCAL,
    )
    action: Mapped[PolicyAction] = mapped_column(
        Enum(PolicyAction, name="policyaction", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    custom_rules: Mapped[list] = mapped_column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))

    overridable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hq_policy_id: Mapped[UUID | None] = mapped_column(nullable=True)
    is_global: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    services: Mapped[list["Service"]] = relationship(
        "Service", secondary=policy_services, lazy="selectin",
    )
