import os
import logging
from typing import Dict, Any

from app.db.client import VBDatabaseClient, create_vb_database_client
from app.db.campaign_dao import CampaignDataAccess
from app.db.contact_dao import ContactDataAccess
from app.db.survey_dao import SurveyDataAccess
from app.db.call_dao import CallDataAccess

# Configure logging
logger = logging.getLogger(__name__)


class VBSystemUtilities:
    """High-level utilities for VB system integration"""
    
    def __init__(self, db_client: VBDatabaseClient):
        self.db = db_client
        self.campaign_dao = CampaignDataAccess(db_client)
        self.contact_dao = ContactDataAccess(db_client)
        self.survey_dao = SurveyDataAccess(db_client)
        self.call_dao = CallDataAccess(db_client)
    
    async def get_instruction(self, campaign_id: str) -> Dict[str, Any]:
        """Get AI agent instructions for a specific campaign"""
        campaign_data = await self.campaign_dao.get_campaign_with_ai_config(campaign_id)
        
        if not campaign_data:
            raise ValueError(f"Campaign {campaign_id} not found or not AI-enabled")
        
        return {
            "campaign_id": campaign_id,
            "instructions": campaign_data.get('system_prompt', ''),
            "persona_config": {
                "name": campaign_data.get('persona_name', ''),
                "voice_config": campaign_data.get('voice_config', {}),
                "personality_traits": campaign_data.get('personality_traits', {}),
                "behavior_settings": campaign_data.get('behavior_settings', {})
            },
            "custom_instructions": campaign_data.get('custom_instructions', '')
        }
    
    async def get_prompt(self, campaign_id: str, contact_id: str) -> str:
        """Generate personalized system prompt for AI agent"""
        campaign_data = await self.campaign_dao.get_campaign_with_ai_config(campaign_id)
        contact_data = await self.contact_dao.get_contact_by_id(contact_id)
        
        if not campaign_data:
            raise ValueError(f"Campaign {campaign_id} not found or not AI-enabled")
        
        if not contact_data:
            raise ValueError(f"Contact {contact_id} not found")
        
        # Base prompt from campaign configuration
        base_prompt = campaign_data.get('system_prompt', '')
        
        # Personalization variables
        contact_name = f"{contact_data.get('first_name', '')} {contact_data.get('last_name', '')}".strip()
        contact_city = contact_data.get('city', '')
        contact_state = contact_data.get('state', '')
        
        # Replace placeholders in prompt
        personalized_prompt = base_prompt.replace('{contact_name}', contact_name)
        personalized_prompt = personalized_prompt.replace('{contact_city}', contact_city)
        personalized_prompt = personalized_prompt.replace('{contact_state}', contact_state)
        personalized_prompt = personalized_prompt.replace('{campaign_name}', campaign_data.get('campaign_name', ''))
        
        # Add custom instructions if available
        custom_instructions = campaign_data.get('custom_instructions', '')
        if custom_instructions:
            personalized_prompt += f"\n\nAdditional Instructions:\n{custom_instructions}"
        
        return personalized_prompt
    
    async def get_openai_config(self, campaign_id: str) -> Dict[str, Any]:
        """Get OpenAI configuration for a campaign"""
        campaign_data = await self.campaign_dao.get_campaign_with_ai_config(campaign_id)
        
        if not campaign_data:
            raise ValueError(f"Campaign {campaign_id} not found or not AI-enabled")
        
        voice_config = campaign_data.get('voice_config', {})
        conversation_settings = campaign_data.get('conversation_settings', {})
        
        return {
            "voice": voice_config.get('voice', 'ash'),
            "temperature": conversation_settings.get('temperature', 0.7),
            "turn_detection": conversation_settings.get('turn_detection', {"type": "server_vad"}),
            "input_audio_transcription": conversation_settings.get(
                'input_audio_transcription', 
                {"model": "whisper-1", "language": "en"}
            ),
            "input_audio_format": "g711_ulaw",
            "output_audio_format": "g711_ulaw",
            "tools": []  # Will be populated with function schemas
        }
    
    async def get_campaign_data(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign details and configuration"""
        campaign_data = await self.campaign_dao.get_campaign_with_ai_config(campaign_id)
        
        if not campaign_data:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        return {
            "campaign": {
                "id": campaign_data.get('campaign_id'),
                "name": campaign_data.get('campaign_name'),
                "description": campaign_data.get('campaign_description'),
                "status": campaign_data.get('campaign_status'),
                "is_ai_agent": campaign_data.get('is_ai_agent')
            },
            "ai_config": {
                "id": campaign_data.get('ai_config_id'),
                "custom_instructions": campaign_data.get('custom_instructions'),
                "system_prompt": campaign_data.get('system_prompt'),
                "conversation_settings": campaign_data.get('conversation_settings')
            },
            "persona": {
                "id": campaign_data.get('persona_id'),
                "name": campaign_data.get('persona_name'),
                "voice_config": campaign_data.get('voice_config'),
                "personality_traits": campaign_data.get('personality_traits'),
                "behavior_settings": campaign_data.get('behavior_settings')
            }
        }
    
    async def get_contact_info(self, contact_id: str) -> Dict[str, Any]:
        """Get contact information for personalization"""
        contact_data = await self.contact_dao.get_contact_by_id(contact_id)
        
        if not contact_data:
            raise ValueError(f"Contact {contact_id} not found")
        
        return {
            "contact": contact_data,
            "preferences": contact_data.get('additional_vars', {}),
            "history": []  # TODO: Implement call history if needed
        }
    
    async def get_survey_config(self, campaign_id: str) -> Dict[str, Any]:
        """Get survey questions and choices for a campaign"""
        survey_data = await self.survey_dao.get_survey_by_campaign(campaign_id)
        
        if not survey_data:
            return {"survey_id": None, "questions": [], "choices": {}}
        
        survey_id = str(survey_data['id'])
        questions = await self.survey_dao.get_survey_questions(survey_id)
        
        choices = {}
        for question in questions:
            question_id = str(question['id'])
            question_choices = await self.survey_dao.get_question_choices(question_id)
            choices[question_id] = question_choices
        
        return {
            "survey_id": survey_id,
            "questions": questions,
            "choices": choices
        }


# Utility function to get VB system utilities
async def get_vb_utilities(database_url: str = None) -> VBSystemUtilities:
    """Get VB system utilities with initialized database client"""
    client = await create_vb_database_client(database_url)
    return VBSystemUtilities(client) 