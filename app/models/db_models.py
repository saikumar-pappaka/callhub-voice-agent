from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime


class CampaignStatus(Enum):
    """Campaign status constants"""
    START = 1
    PAUSE = 2
    STOP = 3
    COMPLETE = 4


class SubscriberStatus(Enum):
    """Subscriber status constants"""
    PENDING = 1
    ACTIVE = 2
    COMPLETED = 3
    FAILED = 4
    OPTED_OUT = 5


@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str
    port: int
    database: str
    user: str
    password: str
    pool_min_size: int = 5
    pool_max_size: int = 20
    
    @classmethod
    def from_url(cls, database_url: str) -> 'DatabaseConfig':
        """Create config from database URL"""
        # Parse database URL: postgresql://user:password@host:port/database
        import urllib.parse
        parsed = urllib.parse.urlparse(database_url)
        
        return cls(
            host=parsed.hostname,
            port=parsed.port or 5432,
            database=parsed.path.lstrip('/'),
            user=parsed.username,
            password=parsed.password
        ) 