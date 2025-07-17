import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.db.client import VBDatabaseClient

# Configure logging
logger = logging.getLogger(__name__)


class CallDataAccess:
    """Data access layer for call-related operations"""
    
    def __init__(self, db_client: VBDatabaseClient):
        self.db = db_client
    
    async def get_call_request(self, call_request_id: str) -> Optional[Dict[str, Any]]:
        """Get call request details by ID"""
        query = """
        SELECT 
            cr.id,
            cr.request_uuid,
            cr.call_id,
            cr.status,
            cr.hangup_cause,
            cr.callerid,
            cr.phone_number,
            cr.timeout,
            cr.created_date,
            cr.updated_date,
            cr.campaign_id,
            cr.subscriber_id,
            cr.user_id
        FROM dialer_callrequest cr
        WHERE cr.id = $1
        """
        
        return await self.db.fetch_one(query, int(call_request_id))
    
    async def update_call_status(self, call_request_id: str, status: int, hangup_cause: str = None) -> bool:
        """Update call request status"""
        query = """
        UPDATE dialer_callrequest 
        SET status = $2, hangup_cause = $3, updated_date = $4
        WHERE id = $1
        """
        
        try:
            await self.db.execute_command(
                query, 
                int(call_request_id), 
                status, 
                hangup_cause, 
                datetime.now(timezone.utc)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update call status: {e}")
            return False
    
    async def add_call_disposition(self, subscriber_id: str, campaign_id: str, disposition_code: str, notes: str = None) -> Optional[str]:
        """Add call disposition"""
        query = """
        INSERT INTO call_disposition (
            powersubscriber_id, campaign_id, disposition_code, notes, created_date
        )
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """
        
        try:
            result = await self.db.fetch_one(
                query,
                int(subscriber_id),
                int(campaign_id),
                disposition_code,
                notes,
                datetime.now(timezone.utc)
            )
            return str(result['id']) if result else None
        except Exception as e:
            logger.error(f"Failed to add call disposition: {e}")
            return None
    
    async def update_subscriber_disposition(self, subscriber_id: str, disposition: str) -> bool:
        """Update PowerSubscriber disposition"""
        query = """
        UPDATE power_subscriber 
        SET disposition = $2, updated_date = $3, last_attempt = $3
        WHERE id = $1
        """
        
        try:
            await self.db.execute_command(
                query, 
                int(subscriber_id), 
                disposition, 
                datetime.now(timezone.utc)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update subscriber disposition: {e}")
            return False 