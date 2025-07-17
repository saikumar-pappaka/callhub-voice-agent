import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.db.client import VBDatabaseClient

# Configure logging
logger = logging.getLogger(__name__)


class ContactDataAccess:
    """Data access layer for contact-related operations"""
    
    def __init__(self, db_client: VBDatabaseClient):
        self.db = db_client
    
    async def get_contact_by_id(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Get contact details by ID"""
        query = """
        SELECT 
            c.id,
            c.first_name,
            c.last_name,
            c.email,
            c.phone_number,
            c.mobile,
            c.status,
            c.city,
            c.state,
            c.country,
            c.zip_code,
            c.created_date,
            c.updated_date,
            c.additional_vars
        FROM dialer_contact c
        WHERE c.id = $1
        """
        
        result = await self.db.fetch_one(query, int(contact_id))
        if result and result.get('additional_vars'):
            # Parse JSON field if it's a string
            if isinstance(result['additional_vars'], str):
                result['additional_vars'] = json.loads(result['additional_vars'])
        
        return result
    
    async def get_power_subscriber(self, subscriber_id: str) -> Optional[Dict[str, Any]]:
        """Get PowerSubscriber details by ID"""
        query = """
        SELECT 
            ps.id,
            ps.contact_id,
            ps.campaign_id,
            ps.duplicate_contact,
            ps.status,
            ps.last_attempt,
            ps.count_attempt,
            ps.disposition,
            ps.created_date,
            ps.updated_date,
            c.first_name,
            c.last_name,
            c.phone_number,
            c.email,
            pc.name as campaign_name
        FROM power_subscriber ps
        JOIN dialer_contact c ON ps.contact_id = c.id
        JOIN power_campaign pc ON ps.campaign_id = pc.id
        WHERE ps.id = $1
        """
        
        return await self.db.fetch_one(query, int(subscriber_id))
    
    async def get_power_subscriber_by_contact_campaign(self, contact_id: str, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get PowerSubscriber by contact and campaign ID"""
        query = """
        SELECT 
            ps.id,
            ps.contact_id,
            ps.campaign_id,
            ps.duplicate_contact,
            ps.status,
            ps.last_attempt,
            ps.count_attempt,
            ps.disposition,
            ps.created_date,
            ps.updated_date
        FROM power_subscriber ps
        WHERE ps.contact_id = $1 AND ps.campaign_id = $2
        """
        
        return await self.db.fetch_one(query, int(contact_id), int(campaign_id))
    
    async def update_contact_status(self, contact_id: str, status: int) -> bool:
        """Update contact status"""
        query = """
        UPDATE dialer_contact 
        SET status = $2, updated_date = $3
        WHERE id = $1
        """
        
        try:
            await self.db.execute_command(query, int(contact_id), status, datetime.now(timezone.utc))
            return True
        except Exception as e:
            logger.error(f"Failed to update contact status: {e}")
            return False
    
    async def add_contact_opt_out(self, contact_id: str, campaign_id: str, reason: str) -> Optional[str]:
        """Add contact to opt-out list"""
        query = """
        INSERT INTO contact_opt_out (contact_id, campaign_id, reason, created_date)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """
        
        try:
            result = await self.db.fetch_one(
                query, 
                int(contact_id), 
                int(campaign_id), 
                reason, 
                datetime.now(timezone.utc)
            )
            return str(result['id']) if result else None
        except Exception as e:
            logger.error(f"Failed to add contact opt-out: {e}")
            return None 