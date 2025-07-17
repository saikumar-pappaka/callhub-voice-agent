import json
import logging
from typing import Dict, Any, Optional

from app.db.client import VBDatabaseClient

# Configure logging
logger = logging.getLogger(__name__)


class CampaignDataAccess:
    """Data access layer for campaign-related operations"""
    
    def __init__(self, db_client: VBDatabaseClient):
        self.db = db_client
    
    async def get_campaign_by_id(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get campaign details by ID"""
        query = """
        SELECT 
            pc.id,
            pc.name,
            pc.description,
            pc.status,
            pc.is_ai_agent,
            pc.ai_agent_config_id,
            pc.user_id,
            pc.callerid,
            pc.frequency,
            pc.maxretry,
            pc.callmaxduration,
            pc.daily_start_time,
            pc.daily_stop_time,
            pc.created_date,
            pc.updated_date,
            u.username,
            u.email
        FROM power_campaign pc
        JOIN auth_user u ON pc.user_id = u.id
        WHERE pc.id = $1
        """
        
        result = await self.db.fetch_one(query, int(campaign_id))
        if result:
            # Convert time fields to string if needed
            if result.get('daily_start_time'):
                result['daily_start_time'] = str(result['daily_start_time'])
            if result.get('daily_stop_time'):
                result['daily_stop_time'] = str(result['daily_stop_time'])
        
        return result
    
    async def get_ai_agent_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """Get AI agent configuration by ID"""
        query = """
        SELECT 
            aac.id,
            aac.persona_id,
            aac.custom_instructions,
            aac.system_prompt,
            aac.conversation_settings,
            aac.created_by,
            aac.created_date,
            aac.updated_date
        FROM ai_agent_config aac
        WHERE aac.id = $1
        """
        
        result = await self.db.fetch_one(query, int(config_id))
        if result and result.get('conversation_settings'):
            # Parse JSON field if it's a string
            if isinstance(result['conversation_settings'], str):
                result['conversation_settings'] = json.loads(result['conversation_settings'])
        
        return result
    
    async def get_ai_agent_persona(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Get AI agent persona by ID"""
        query = """
        SELECT 
            aap.id,
            aap.name,
            aap.voice_config,
            aap.personality_traits,
            aap.behavior_settings,
            aap.is_active,
            aap.created_by,
            aap.created_date,
            aap.updated_date
        FROM ai_agent_persona aap
        WHERE aap.id = $1 AND aap.is_active = true
        """
        
        result = await self.db.fetch_one(query, int(persona_id))
        if result:
            # Parse JSON fields if they're strings
            json_fields = ['voice_config', 'personality_traits', 'behavior_settings']
            for field in json_fields:
                if result.get(field) and isinstance(result[field], str):
                    result[field] = json.loads(result[field])
        
        return result
    
    async def get_campaign_with_ai_config(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get campaign with complete AI configuration"""
        query = """
        SELECT 
            pc.id as campaign_id,
            pc.name as campaign_name,
            pc.description as campaign_description,
            pc.status as campaign_status,
            pc.is_ai_agent,
            pc.user_id,
            u.username,
            u.email,
            aac.id as ai_config_id,
            aac.custom_instructions,
            aac.system_prompt,
            aac.conversation_settings,
            aap.id as persona_id,
            aap.name as persona_name,
            aap.voice_config,
            aap.personality_traits,
            aap.behavior_settings
        FROM power_campaign pc
        JOIN auth_user u ON pc.user_id = u.id
        LEFT JOIN ai_agent_config aac ON pc.ai_agent_config_id = aac.id
        LEFT JOIN ai_agent_persona aap ON aac.persona_id = aap.id
        WHERE pc.id = $1 AND pc.is_ai_agent = true
        """
        
        result = await self.db.fetch_one(query, int(campaign_id))
        if result:
            # Parse JSON fields
            json_fields = ['conversation_settings', 'voice_config', 'personality_traits', 'behavior_settings']
            for field in json_fields:
                if result.get(field) and isinstance(result[field], str):
                    result[field] = json.loads(result[field])
        
        return result 