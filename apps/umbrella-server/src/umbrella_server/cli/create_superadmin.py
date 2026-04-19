"""Создание первого superadmin.

Запуск:
    pdm run python -m umbrella_server.cli.create_superadmin \\
        --email admin@umbrella.su --password 'SuperSecret123' --name 'Root'

Идемпотентно: если админ с таким email уже есть — ничего не делает.
"""

import argparse
import asyncio
import sys

from umbrella_server.core.config import get_settings
from umbrella_server.core.logging import configure_logging, get_logger
from umbrella_server.db.session import create_engine, create_session_factory
from umbrella_server.domains.auth.models import AdminRole
from umbrella_server.domains.auth.repository import AdminRepository
from umbrella_server.domains.auth.security import hash_password


async def run(email: str, password: str, full_name: str | None) -> int:
    settings = get_settings()
    configure_logging(settings)
    logger = get_logger(__name__)

    engine = create_engine(settings)
    factory = create_session_factory(engine)

    try:
        async with factory() as session:
            repo = AdminRepository(session)

            existing = await repo.get_by_email(email)
            if existing is not None:
                logger.warning("superadmin_already_exists", email=email, admin_id=existing.id)
                return 0

            admin = await repo.create(
                email=email,
                password_hash=hash_password(password),
                role=AdminRole.SUPERADMIN,
                full_name=full_name,
            )
            await session.commit()
            logger.info("superadmin_created", admin_id=admin.id, email=email)
            return 0
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create initial superadmin")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", default=None)
    args = parser.parse_args()

    exit_code = asyncio.run(run(args.email, args.password, args.name))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()