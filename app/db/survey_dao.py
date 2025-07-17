import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.db.client import VBDatabaseClient

# Configure logging
logger = logging.getLogger(__name__)


class SurveyDataAccess:
    """Data access layer for survey-related operations"""
    
    def __init__(self, db_client: VBDatabaseClient):
        self.db = db_client
    
    async def get_survey_by_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get survey configuration for a campaign"""
        query = """
        SELECT 
            s.id,
            s.name,
            s.description,
            s.created_date,
            s.updated_date
        FROM survey_survey s
        JOIN power_campaign pc ON s.id = pc.object_id
        WHERE pc.id = $1 AND pc.content_type_id = (
            SELECT id FROM django_content_type WHERE model = 'survey'
        )
        """
        
        return await self.db.fetch_one(query, int(campaign_id))
    
    async def get_survey_questions(self, survey_id: str) -> List[Dict[str, Any]]:
        """Get all questions for a survey"""
        query = """
        SELECT 
            sq.id,
            sq.question_text,
            sq.question_type,
            sq.order_position,
            sq.is_required,
            sq.created_date
        FROM survey_question sq
        WHERE sq.survey_id = $1
        ORDER BY sq.order_position
        """
        
        return await self.db.execute_query(query, int(survey_id))
    
    async def get_question_choices(self, question_id: str) -> List[Dict[str, Any]]:
        """Get choices for a specific question"""
        query = """
        SELECT 
            sc.id,
            sc.choice_text,
            sc.choice_value,
            sc.order_position
        FROM survey_choice sc
        WHERE sc.question_id = $1
        ORDER BY sc.order_position
        """
        
        return await self.db.execute_query(query, int(question_id))
    
    async def save_survey_response(self, subscriber_id: str, question_id: str, choice_id: str = None, answer_text: str = None) -> Optional[str]:
        """Save survey response"""
        query = """
        INSERT INTO survey_response (
            powersubscriber_id, question_id, choice_id, answer_text, created_date
        )
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id
        """
        
        try:
            result = await self.db.fetch_one(
                query,
                int(subscriber_id),
                int(question_id),
                int(choice_id) if choice_id else None,
                answer_text,
                datetime.now(timezone.utc)
            )
            return str(result['id']) if result else None
        except Exception as e:
            logger.error(f"Failed to save survey response: {e}")
            return None 