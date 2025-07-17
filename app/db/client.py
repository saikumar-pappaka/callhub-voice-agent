import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
import asyncpg
from asyncpg import Pool

from app.models.db_models import DatabaseConfig

# Configure logging
logger = logging.getLogger(__name__)


class VBDatabaseClient:
    """Database client for VB System integration"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[Pool] = None
        self._connection_string = self._build_connection_string()
    
    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string"""
        return (
            f"postgresql://{self.config.user}:{self.config.password}@"
            f"{self.config.host}:{self.config.port}/{self.config.database}"
        )
    
    async def connect(self) -> None:
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self._connection_string,
                min_size=self.config.pool_min_size,
                max_size=self.config.pool_max_size,
                command_timeout=60
            )
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query, *args)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Args: {args}")
                raise
    
    async def execute_command(self, query: str, *args) -> str:
        """Execute INSERT/UPDATE/DELETE command"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            try:
                result = await conn.execute(query, *args)
                return result
            except Exception as e:
                logger.error(f"Command execution failed: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Args: {args}")
                raise
    
    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute query and return first result"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, *args)
                return dict(row) if row else None
            except Exception as e:
                logger.error(f"Fetch one failed: {e}")
                raise


# Factory function to create database client
async def create_vb_database_client(database_url: str = None) -> VBDatabaseClient:
    """Create and initialize VB database client"""
    if not database_url:
        database_url = os.getenv('VB_DATABASE_URL')
        if not database_url:
            raise ValueError("VB_DATABASE_URL environment variable is required")
    
    config = DatabaseConfig.from_url(database_url)
    client = VBDatabaseClient(config)
    await client.connect()
    return client 