import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.audit   import router as audit_router
from routes.leads   import router as leads_router
from routes.auth    import router as auth_router
from routes.admin   import router as admin_router
from routes.payment import router as payment_router
from routes.portal  import router as portal_router
from database.connection import create_tables, test_connection

if os.getenv("ENVIRONMENT") == "production":
    sentry_dsn = os.getenv("SENTRY_DSN", "").strip()
    if sentry_dsn:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FastApiIntegration()],
        )


def _load_allowed_origins() -> list[str]:
    configured = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]

    defaults = [
        os.getenv("FRONTEND_URL", "http://localhost:5173"),
        os.getenv("ADMIN_URL", "http://localhost:5174"),
        "http://localhost:3000",
    ]
    seen: list[str] = []
    for origin in defaults:
        cleaned = origin.strip().rstrip("/")
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return seen


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Aidbro] Starting up...")
    db_ok = await test_connection()
    if db_ok:
        await create_tables()
    else:
        print("[Aidbro] WARNING: DB unavailable — some features won't work")
    yield
    print("[Aidbro] Shutting down...")


app = FastAPI(
    title="Aidbro Digital Health API",
    description="AI-powered digital presence analyzer + Stage 4 premium system",
    version="3.0.0",
    lifespan=lifespan,
    docs_url=None if os.getenv("ENVIRONMENT") == "production" else "/docs",
    redoc_url=None if os.getenv("ENVIRONMENT") == "production" else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_load_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(audit_router,   prefix="/api")
app.include_router(leads_router,   prefix="/api")
app.include_router(auth_router,    prefix="/api")
app.include_router(admin_router,   prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(portal_router,  prefix="/api")


@app.get("/")
def root():
    return {
        "status":  "Aidbro Digital Health API is running",
        "version": "3.0.0",
        "docs":    "/docs",
    }
