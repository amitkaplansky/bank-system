from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from .config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection manager for Consumer Service"""
    
    def __init__(self):
        self.database_url = settings.DATABASE_URL
        
        self.engine = create_async_engine(
            self.database_url,
            echo=settings.DEBUG,
            pool_size=10,
            max_overflow=0,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        
        self.SessionLocal = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic cleanup"""
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
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def close(self):
        """Close database connections"""
        await self.engine.dispose()
        logger.info("Database connections closed")

db_manager = DatabaseManager()