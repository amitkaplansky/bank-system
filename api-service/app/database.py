from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from .config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    
    def __init__(self):
        self.database_url = settings.DATABASE_URL
        
        self.engine = create_async_engine(
            self.database_url,
            echo=settings.DEBUG,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,
            pool_recycle=settings.DB_POOL_RECYCLE,
        )
        
        self.SessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session with automatic cleanup
        """
        async with self.SessionLocal() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> bool:
        """Check if database is accessible"""
        try:
            async with self.get_session() as session:
                result = await session.execute("SELECT 1")
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def close(self):
        """Close database connections"""
        await self.engine.dispose()
        logger.info("Database connections closed")

# Global database manager instance
db_manager = DatabaseManager()

# FastAPI dependency for getting database session
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for getting database session
    Usage:
        @app.get("/endpoint")
        async def endpoint(session: AsyncSession = Depends(get_db_session)):
            # Use session here
    """
    async with db_manager.get_session() as session:
        yield session