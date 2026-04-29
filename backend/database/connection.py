"""Database connection management with async SQLAlchemy.

Provides async engine, session factory, and connection pooling for PostgreSQL.
All operations are async/await compatible.
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

# PostgreSQL async URL pattern: postgresql+asyncpg://user:password@host:port/database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/sentryiq",
)

# Connection pool settings
POOL_SIZE = 20  # Concurrent connections
MAX_OVERFLOW = 10  # Additional connections if pool is exhausted
POOL_RECYCLE = 3600  # Recycle connections after 1 hour
POOL_PRE_PING = True  # Verify connection before use


async def get_engine() -> AsyncEngine:
    """Create async SQLAlchemy engine with connection pooling.
    
    Returns:
        AsyncEngine configured for PostgreSQL with asyncpg driver.
    """
    engine: AsyncEngine = create_async_engine(
        DATABASE_URL,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        pool_size=POOL_SIZE,
        max_overflow=MAX_OVERFLOW,
        pool_recycle=POOL_RECYCLE,
        pool_pre_ping=POOL_PRE_PING,
    )
    return engine


# Create async session factory
async_session_factory = sessionmaker(
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db(engine: AsyncEngine) -> None:
    """Initialize database tables.
    
    Creates all tables defined in models.Base.metadata if they don't exist.
    This is typically called once on application startup.
    
    Args:
        engine: AsyncEngine instance.
    """
    from .models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session for dependency injection.
    
    Yields:
        AsyncSession instance. Automatically closed after use.
        
    Typical FastAPI usage:
        @app.get("/items")
        async def read_items(session: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
