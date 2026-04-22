import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(dotenv_path=ENV_PATH)

# ── Build the async database URL ─────────────────────────────────────────────
# SQLAlchemy async requires postgresql+asyncpg:// instead of postgresql://
DATABASE_URL = os.getenv("DATABASE_URL", "")

if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql+asyncpg://"):
    ASYNC_DATABASE_URL = DATABASE_URL
else:
    # Fallback for development — uses the values directly
    ASYNC_DATABASE_URL = (
        "postgresql+asyncpg://postgres:aidbro2026@localhost:5432/aidbro_db"
    )

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,          # Set True temporarily if you want SQL logs
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections are alive before using
)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# ── Base class for all ORM models ─────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Dependency for FastAPI routes ─────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """
    FastAPI dependency — yields a DB session per request.
    Usage in routes:
        async def my_route(db: AsyncSession = Depends(get_db)):
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Create all tables (called on startup) ─────────────────────────────────────
async def create_tables():
    """Create all tables defined in models.py if they don't exist."""
    from database import models  # noqa: F401 — import to register models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[DB] Tables verified / created successfully")


# ── Test connection ───────────────────────────────────────────────────────────
async def test_connection():
    """Quick connection test — called on startup."""
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        print("[DB] PostgreSQL connection successful")
        return True
    except Exception as e:
        print(f"[DB] Connection failed: {e}")
        print("[DB] Check DATABASE_URL in your .env file")
        return False
