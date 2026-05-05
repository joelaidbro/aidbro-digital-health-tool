from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from database import crud
from database.connection import get_db
from database.models import AdminUser, UserAccount
from utils.auth_utils import decode_admin_token, decode_user_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_optional_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[UserAccount]:
    if not token:
        return None

    payload = decode_user_token(token)
    if not payload or payload.get("role") != "client":
        return None

    email = payload.get("sub", "")
    if not email:
        return None
    return await crud.get_user_by_email(db, email)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserAccount:
    user = await get_optional_current_user(token, db)
    if not user:
        raise HTTPException(401, "Invalid or expired user token.")
    return user


async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    if not token:
        raise HTTPException(401, "Admin authentication required.")

    payload = decode_admin_token(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired admin token.")

    admin = await crud.get_admin_by_email(db, payload.get("sub", ""))
    if not admin or not admin.is_active:
        raise HTTPException(401, "Admin account not found or inactive.")
    return admin
