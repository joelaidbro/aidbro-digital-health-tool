import argparse
import asyncio
import getpass

from sqlalchemy import func, select

from database.connection import AsyncSessionLocal, create_tables
from database.models import AdminUser
from utils.auth_utils import hash_password


def _prompt_if_missing(value: str | None, label: str, secret: bool = False) -> str:
    if value:
        return value
    return getpass.getpass(f"{label}: ") if secret else input(f"{label}: ").strip()


async def main():
    parser = argparse.ArgumentParser(description="Create the first Aidbro admin account.")
    parser.add_argument("--name", help="Admin full name")
    parser.add_argument("--email", help="Admin email address")
    parser.add_argument(
        "--role",
        default="super_admin",
        choices=["super_admin", "manager", "analyst"],
        help="Admin role to create",
    )
    parser.add_argument("--password", help="Admin password")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Create the account even if another admin already exists",
    )
    args = parser.parse_args()

    await create_tables()

    name = _prompt_if_missing(args.name, "Full name")
    email = _prompt_if_missing(args.email, "Email").lower()
    password = _prompt_if_missing(args.password, "Password", secret=True)

    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters.")

    async with AsyncSessionLocal() as db:
        existing_count = (
            await db.execute(select(func.count(AdminUser.id)))
        ).scalar_one()
        if existing_count > 0 and not args.force:
            raise SystemExit(
                "Admin accounts already exist. Re-run with --force if you really want to add another one."
            )

        existing_email = (
            await db.execute(
                select(AdminUser).where(func.lower(AdminUser.email) == email)
            )
        ).scalar_one_or_none()
        if existing_email:
            raise SystemExit("An admin account with this email already exists.")

        admin = AdminUser(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=args.role,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)

    print("Admin account created successfully.")
    print(f"Name : {admin.name}")
    print(f"Email: {admin.email}")
    print(f"Role : {admin.role}")


if __name__ == "__main__":
    asyncio.run(main())
