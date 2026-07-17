"""
Auth Routes
============
POST /api/auth/register        — Email/password registration
POST /api/auth/login           — Email/password login
POST /api/auth/refresh         — Refresh access token
GET  /api/auth/google          — Start Google OAuth flow
GET  /api/auth/google/callback — Google OAuth callback
GET  /api/auth/me              — Get current user info
POST /api/auth/logout          — Clear tokens
POST /api/auth/admin/login     — Admin login
"""

import os
import httpx
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database import crud
from database.models import AuditClient
from main import limiter
from utils.auth_utils import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token,
)

router = APIRouter()

# ── Google OAuth config ───────────────────────────────────────────────────────
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
FRONTEND_URL         = os.getenv("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL          = os.getenv("BACKEND_URL", "http://localhost:8000")
GOOGLE_REDIRECT_URI  = f"{BACKEND_URL}/api/auth/google/callback"
GOOGLE_AUTH_URL      = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL     = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL  = "https://www.googleapis.com/oauth2/v3/userinfo"

COOKIE_SETTINGS = {
    "httponly": True,
    "secure":   os.getenv("ENVIRONMENT", "development") == "production",
    "samesite": "lax",
    "max_age":  7 * 24 * 3600,
}


# ── Request / Response models ─────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email:    EmailStr
    password: str
    name:     Optional[str] = None


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class AdminLoginRequest(BaseModel):
    email:    EmailStr
    password: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _token_response(
    email: str,
    role: str,
    name: str = "",
    has_paid: bool = False,
    audit_credits: int = 0,
    is_test_account: bool = False,
):
    access  = create_access_token(email, role)
    refresh = create_refresh_token(email, role)
    return {
        "access_token":  access,
        "refresh_token": refresh,
        "token_type":    "bearer",
        "user": {
            "email":           email,
            "name":            name,
            "role":            role,
            "has_paid":        has_paid,
            "audit_credits":   audit_credits,
            "is_test_account": is_test_account,
        }
    }


def _get_token_from_request(request: Request) -> Optional[str]:
    """Extract bearer token from Authorization header or cookie."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return request.cookies.get("access_token")


async def _ensure_shadow_client(
    db: AsyncSession,
    email: str,
    password_hash: str = "",
):
    client = await crud.get_client_by_email(db, email)
    if client:
        if password_hash and not client.password_hash:
            client.password_hash = password_hash
            await db.flush()
        return client

    client = AuditClient(
        email=email,
        password_hash=password_hash,
        audit_status="unsubscribed",
        plan_type="none",
    )
    db.add(client)
    await db.flush()
    await db.refresh(client)
    return client


# ── EMAIL / PASSWORD REGISTER ─────────────────────────────────────────────────

@router.post("/auth/register")
@limiter.limit("10/minute")
async def register(request: Request, req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new client account.
    Creates account but no paid access yet — payment unlocks the portal.
    """
    existing_user = await crud.get_user_by_email(db, req.email)
    if existing_user:
        raise HTTPException(400, "An account with this email already exists.")
    existing_client = await crud.get_client_by_email(db, req.email)
    if existing_client and existing_client.password_hash:
        raise HTTPException(400, "An account with this email already exists.")

    if len(req.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters.")

    password_hash = hash_password(req.password)
    user = await crud.create_user_account(
        db,
        email=req.email,
        password_hash=password_hash,
        name=req.name or "",
        auth_provider="email",
    )
    await crud.update_user_last_login(db, user.id)
    await crud.create_user_activity(
        db,
        user.id,
        "register",
        {"auth_provider": "email"},
    )

    if existing_client:
        existing_client.password_hash = password_hash
        existing_client.audit_status = existing_client.audit_status or "unsubscribed"
        existing_client.plan_type = existing_client.plan_type or "none"
        await db.flush()
    else:
        await _ensure_shadow_client(db, req.email, password_hash)

    data = _token_response(
        req.email, "client", req.name or "",
        has_paid=False,
        audit_credits=user.audit_credits,
        is_test_account=user.is_test_account,
    )
    return JSONResponse(content={"success": True, **data})


# ── EMAIL / PASSWORD LOGIN ────────────────────────────────────────────────────

@router.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, req: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_email(db, req.email)

    if user and user.password_hash:
        if not verify_password(req.password, user.password_hash):
            raise HTTPException(401, "Invalid email or password.")
        await crud.update_user_last_login(db, user.id)
        await crud.create_user_activity(db, user.id, "login", {"source": "email"})
        client = await _ensure_shadow_client(db, req.email, user.password_hash)
        has_paid = client.paid_at is not None
        data = _token_response(
            req.email, "client", name=user.name or "", has_paid=has_paid,
            audit_credits=user.audit_credits,
            is_test_account=user.is_test_account,
        )
        return JSONResponse(content={"success": True, **data})

    client = await crud.get_client_by_email(db, req.email)
    if not client or not client.password_hash:
        raise HTTPException(401, "Invalid email or password.")
    if not verify_password(req.password, client.password_hash):
        raise HTTPException(401, "Invalid email or password.")

    migrated_user = user or await crud.create_user_account(
        db,
        email=req.email,
        password_hash=client.password_hash,
        name="",
        auth_provider="email",
    )
    await crud.update_user_last_login(db, migrated_user.id)
    await crud.create_user_activity(db, migrated_user.id, "login", {"source": "legacy_client"})

    has_paid = client.paid_at is not None
    data = _token_response(
        req.email, "client", name=migrated_user.name or "", has_paid=has_paid,
        audit_credits=migrated_user.audit_credits,
        is_test_account=migrated_user.is_test_account,
    )
    return JSONResponse(content={"success": True, **data})


# ── TOKEN REFRESH ─────────────────────────────────────────────────────────────

@router.post("/auth/refresh")
async def refresh_token(request: Request, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("refresh_token") or (
        request.headers.get("Authorization", "").replace("Bearer ", "")
    )
    if not token:
        raise HTTPException(401, "No refresh token provided.")

    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid or expired refresh token.")

    email = payload.get("sub")
    role  = payload.get("role", "client")

    if role == "client":
        user = await crud.get_user_by_email(db, email)
        client = await crud.get_client_by_email(db, email)
        if not user and not client:
            raise HTTPException(401, "Account not found.")
        has_paid = client.paid_at is not None if client else False
        if user:
            await crud.update_user_last_login(db, user.id)
            await crud.create_user_activity(db, user.id, "refresh", {"has_paid": has_paid})
        data = _token_response(
            email, role, name=user.name if user else "", has_paid=has_paid,
            audit_credits=user.audit_credits if user else 0,
            is_test_account=user.is_test_account if user else False,
        )
    else:
        admin = await crud.get_admin_by_email(db, email)
        if not admin or not admin.is_active:
            raise HTTPException(401, "Admin account not found or inactive.")
        data = _token_response(email, role, name=admin.name)

    return JSONResponse(content={"success": True, **data})


# ── GET CURRENT USER ──────────────────────────────────────────────────────────

@router.get("/auth/me")
async def get_me(request: Request, db: AsyncSession = Depends(get_db)):
    token = _get_token_from_request(request)
    if not token:
        raise HTTPException(401, "Not authenticated.")

    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Invalid or expired token.")

    email = payload.get("sub")
    role  = payload.get("role", "client")

    if role == "client":
        user = await crud.get_user_by_email(db, email)
        client = await crud.get_client_by_email(db, email)
        if not user and not client:
            raise HTTPException(404, "Account not found.")
        return JSONResponse(content={
            "email":           email,
            "name":            user.name if user else "",
            "role":            "client",
            "has_paid":        client.paid_at is not None if client else False,
            "audit_status":    client.audit_status if client else "unsubscribed",
            "plan_type":       client.plan_type if client else "none",
            "audit_credits":   user.audit_credits if user else 0,
            "is_test_account": user.is_test_account if user else False,
        })
    else:
        admin = await crud.get_admin_by_email(db, email)
        if not admin:
            raise HTTPException(404, "Admin not found.")
        return JSONResponse(content={
            "email": admin.email,
            "name":  admin.name,
            "role":  admin.role,
        })


# ── GOOGLE OAUTH — START ──────────────────────────────────────────────────────

@router.get("/auth/google")
async def google_auth_start():
    """Redirect user to Google's OAuth consent screen."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(500, "Google OAuth not configured. Add GOOGLE_CLIENT_ID to .env")

    import urllib.parse
    params = urllib.parse.urlencode({
        "client_id":     GOOGLE_CLIENT_ID,
        "redirect_uri":  GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope":         "openid email profile",
        "access_type":   "offline",
        "prompt":        "select_account",
    })
    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{params}")


# ── GOOGLE OAUTH — CALLBACK ───────────────────────────────────────────────────

@router.get("/auth/google/callback")
async def google_auth_callback(
    code: Optional[str] = None,
    error: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Google sends the user back here after they approve.
    Exchange code for tokens, get user info, create/find account.
    Redirect to frontend with tokens as query params
    (frontend stores them in memory / context).
    """
    if error or not code:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/auth?error=google_denied"
        )

    try:
        async with httpx.AsyncClient() as client:
            # ── Exchange code for tokens ──────────────────────────────────
            token_res = await client.post(GOOGLE_TOKEN_URL, data={
                "code":          code,
                "client_id":     GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri":  GOOGLE_REDIRECT_URI,
                "grant_type":    "authorization_code",
            })
            token_data = token_res.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise ValueError("No access token from Google")

            # ── Fetch user info ────────────────────────────────────────────
            user_res  = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            user_info = user_res.json()

        email = user_info.get("email")
        name  = user_info.get("name", "")

        if not email:
            return RedirectResponse(url=f"{FRONTEND_URL}/auth?error=no_email")

        # ── Find or create client account ─────────────────────────────────
        user = await crud.get_user_by_email(db, email)
        if not user:
            user = await crud.create_user_account(
                db,
                email=email,
                password_hash="",
                name=name,
                auth_provider="google",
            )
        elif name and not user.name:
            user.name = name
            if not user.auth_provider:
                user.auth_provider = "google"
            await db.flush()

        await crud.update_user_last_login(db, user.id)
        await crud.create_user_activity(db, user.id, "login", {"source": "google"})

        existing = await _ensure_shadow_client(db, email, "")
        has_paid = existing.paid_at is not None

        # ── Create JWT and redirect to frontend ───────────────────────────
        jwt_token     = create_access_token(email, "client")
        refresh       = create_refresh_token(email, "client")

        import urllib.parse
        params = urllib.parse.urlencode({
            "token":           jwt_token,
            "refresh":         refresh,
            "email":           email,
            "name":            name,
            "has_paid":        str(has_paid).lower(),
            "audit_credits":   str(user.audit_credits),
            "is_test_account": str(user.is_test_account).lower(),
        })
        return RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?{params}")

    except Exception as e:
        print(f"[Google OAuth] Error: {e}")
        return RedirectResponse(url=f"{FRONTEND_URL}/auth?error=oauth_failed")


# ── LOGOUT ────────────────────────────────────────────────────────────────────

@router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return JSONResponse(content={"success": True})


# ── ADMIN LOGIN ───────────────────────────────────────────────────────────────

@router.post("/auth/admin/login")
@limiter.limit("3 per 5 minutes")
async def admin_login(request: Request, req: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    admin = await crud.get_admin_by_email(db, req.email)
    if not admin or not admin.is_active:
        raise HTTPException(401, "Invalid credentials.")
    if not verify_password(req.password, admin.password_hash):
        raise HTTPException(401, "Invalid credentials.")

    await crud.update_admin_last_login(db, admin.id)
    data = _token_response(req.email, admin.role, name=admin.name)
    return JSONResponse(content={"success": True, **data})
