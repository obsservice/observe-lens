"""Reset the configured bootstrap administrator password without deleting data."""

import asyncio

from sqlalchemy import select

from observelens_auth.core.config import get_settings
from observelens_auth.core.security import hash_password
from observelens_auth.db.models import User
from observelens_auth.db.session import SessionLocal


async def reset_password() -> None:
    settings = get_settings()
    async with SessionLocal() as session:
        user = await session.scalar(
            select(User).where(User.name == settings.bootstrap_admin_username)
        )
        if user is None:
            raise RuntimeError(
                f"Bootstrap administrator '{settings.bootstrap_admin_username}' does not exist. "
                "Start the service once to create it."
            )
        user.password_hash = hash_password(settings.bootstrap_admin_password.get_secret_value())
        await session.commit()
    print(f"Reset password for bootstrap administrator '{settings.bootstrap_admin_username}'.")


if __name__ == "__main__":
    asyncio.run(reset_password())
