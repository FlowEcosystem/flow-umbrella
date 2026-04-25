import enum
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from umbrella_server.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class AdminRole(str, enum.Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    VIEWER = "viewer"


class Admin(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "admins"

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[AdminRole] = mapped_column(
        Enum(AdminRole, name="admin_role", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AdminRole.ADMIN,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    avatar_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        back_populates="admin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # UNIQUE только среди активных — чтобы можно было пересоздать
    # email после soft-delete.
    __table_args__ = (
        Index(
            "uq_admins_email_active",
            "email",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )


class RefreshToken(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "refresh_tokens"

    admin_id: Mapped[UUID] = mapped_column(
        ForeignKey("admins.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 max = 45
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    admin: Mapped[Admin] = relationship(back_populates="refresh_tokens")

    __table_args__ = (
        # Быстрый поиск валидных токенов по hash.
        Index("ix_refresh_tokens_token_hash", "token_hash"),
        # Для cleanup-задачи: SELECT WHERE expires_at < now().
        Index("ix_refresh_tokens_expires_at", "expires_at"),
    )