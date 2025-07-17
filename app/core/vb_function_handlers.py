"""VB System function handlers for integration with OpenAI's Realtime API."""
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
import json

from app.models import FunctionHandler
from app.services.vb_system import get_vb_utilities

# Configure logging
logger = logging.getLogger(__name__)

# Function registry
vb_functions: List[FunctionHandler] = []


# Define handler for get_campaign_info
async def get_campaign_info(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get campaign details for a specific campaign ID."""
    try:
        campaign_id = args.get("campaign_id")
        if not campaign_id:
            return {"error": "Campaign ID is required"}
        
        utils = await get_vb_utilities()
        campaign_data = await utils.get_campaign_data(campaign_id)
        return campaign_data
    except ValueError as ve:
        logger.error(f"Value error in get_campaign_info: {ve}")
        return {"error": str(ve)}
    except Exception as e:
        logger.error(f"Error in get_campaign_info: {e}")
        return {"error": f"Failed to get campaign info: {str(e)}"}


# Define handler for get_contact_info
async def get_contact_info(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get contact details for a specific contact ID."""
    try:
        contact_id = args.get("contact_id")
        if not contact_id:
            return {"error": "Contact ID is required"}
        
        utils = await get_vb_utilities()
        contact_data = await utils.get_contact_info(contact_id)
        return contact_data
    except ValueError as ve:
        logger.error(f"Value error in get_contact_info: {ve}")
        return {"error": str(ve)}
    except Exception as e:
        logger.error(f"Error in get_contact_info: {e}")
        return {"error": f"Failed to get contact info: {str(e)}"}


# Define handler for get_survey_questions
async def get_survey_questions(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get survey questions for a specific campaign ID."""
    try:
        campaign_id = args.get("campaign_id")
        if not campaign_id:
            return {"error": "Campaign ID is required"}
        
        utils = await get_vb_utilities()
        survey_data = await utils.get_survey_config(campaign_id)
        return survey_data
    except ValueError as ve:
        logger.error(f"Value error in get_survey_questions: {ve}")
        return {"error": str(ve)}
    except Exception as e:
        logger.error(f"Error in get_survey_questions: {e}")
        return {"error": f"Failed to get survey questions: {str(e)}"}


# Define handler for save_survey_response
async def save_survey_response(args: Dict[str, Any]) -> Dict[str, Any]:
    """Save a survey response for a specific subscriber."""
    try:
        subscriber_id = args.get("subscriber_id")
        question_id = args.get("question_id")
        choice_id = args.get("choice_id")
        answer_text = args.get("answer_text")
        
        if not subscriber_id or not question_id:
            return {"error": "Subscriber ID and question ID are required"}
        
        utils = await get_vb_utilities()
        response_id = await utils.survey_dao.save_survey_response(
            subscriber_id, question_id, choice_id, answer_text
        )
        
        if response_id:
            return {
                "status": "success",
                "response_id": response_id
            }
        else:
            return {"error": "Failed to save survey response"}
    except Exception as e:
        logger.error(f"Error in save_survey_response: {e}")
        return {"error": f"Failed to save survey response: {str(e)}"}


# Define handler for update_subscriber_disposition
async def update_subscriber_disposition(args: Dict[str, Any]) -> Dict[str, Any]:
    """Update subscriber disposition code."""
    try:
        subscriber_id = args.get("subscriber_id")
        disposition = args.get("disposition")
        
        if not subscriber_id or not disposition:
            return {"error": "Subscriber ID and disposition code are required"}
        
        utils = await get_vb_utilities()
        success = await utils.call_dao.update_subscriber_disposition(subscriber_id, disposition)
        
        if success:
            return {
                "status": "success",
                "message": "Subscriber disposition updated"
            }
        else:
            return {"error": "Failed to update subscriber disposition"}
    except Exception as e:
        logger.error(f"Error in update_subscriber_disposition: {e}")
        return {"error": f"Failed to update subscriber disposition: {str(e)}"}


# Define handler for add_contact_opt_out
async def add_contact_opt_out(args: Dict[str, Any]) -> Dict[str, Any]:
    """Add contact to opt-out list."""
    try:
        contact_id = args.get("contact_id")
        campaign_id = args.get("campaign_id")
        reason = args.get("reason", "User opted out during call")
        
        if not contact_id or not campaign_id:
            return {"error": "Contact ID and campaign ID are required"}
        
        utils = await get_vb_utilities()
        opt_out_id = await utils.contact_dao.add_contact_opt_out(contact_id, campaign_id, reason)
        
        if opt_out_id:
            # Also update contact status
            await utils.contact_dao.update_contact_status(contact_id, 5)  # 5 = OPTED_OUT from enum
            
            return {
                "status": "success",
                "opt_out_id": opt_out_id,
                "message": "Contact successfully opted out"
            }
        else:
            return {"error": "Failed to opt out contact"}
    except Exception as e:
        logger.error(f"Error in add_contact_opt_out: {e}")
        return {"error": f"Failed to opt out contact: {str(e)}"}


# Define schemas for the functions
get_campaign_info_schema = {
    "name": "get_campaign_info",
    "type": "function",
    "description": "Get details about a specific campaign.",
    "parameters": {
        "type": "object",
        "properties": {
            "campaign_id": {
                "type": "string",
                "description": "The ID of the campaign to retrieve information for."
            }
        },
        "required": ["campaign_id"]
    }
}

get_contact_info_schema = {
    "name": "get_contact_info",
    "type": "function",
    "description": "Get information about a specific contact.",
    "parameters": {
        "type": "object",
        "properties": {
            "contact_id": {
                "type": "string",
                "description": "The ID of the contact to retrieve information for."
            }
        },
        "required": ["contact_id"]
    }
}

get_survey_questions_schema = {
    "name": "get_survey_questions",
    "type": "function",
    "description": "Get survey questions for a specific campaign.",
    "parameters": {
        "type": "object",
        "properties": {
            "campaign_id": {
                "type": "string",
                "description": "The ID of the campaign to retrieve survey questions for."
            }
        },
        "required": ["campaign_id"]
    }
}

save_survey_response_schema = {
    "name": "save_survey_response",
    "type": "function",
    "description": "Save a survey response for a specific subscriber.",
    "parameters": {
        "type": "object",
        "properties": {
            "subscriber_id": {
                "type": "string",
                "description": "The ID of the subscriber (participant)."
            },
            "question_id": {
                "type": "string",
                "description": "The ID of the question being answered."
            },
            "choice_id": {
                "type": "string",
                "description": "The ID of the choice selected by the subscriber (optional for free text responses)."
            },
            "answer_text": {
                "type": "string",
                "description": "The free text answer provided by the subscriber (optional for choice-based questions)."
            }
        },
        "required": ["subscriber_id", "question_id"]
    }
}

update_subscriber_disposition_schema = {
    "name": "update_subscriber_disposition",
    "type": "function",
    "description": "Update the disposition code for a subscriber (call outcome).",
    "parameters": {
        "type": "object",
        "properties": {
            "subscriber_id": {
                "type": "string",
                "description": "The ID of the subscriber."
            },
            "disposition": {
                "type": "string",
                "description": "The disposition code to set (e.g., COMPLETED, NO_ANSWER, BUSY, etc.)."
            }
        },
        "required": ["subscriber_id", "disposition"]
    }
}

add_contact_opt_out_schema = {
    "name": "add_contact_opt_out",
    "type": "function",
    "description": "Add a contact to the opt-out list to prevent future calls.",
    "parameters": {
        "type": "object",
        "properties": {
            "contact_id": {
                "type": "string",
                "description": "The ID of the contact to opt out."
            },
            "campaign_id": {
                "type": "string",
                "description": "The ID of the campaign the contact is opting out from."
            },
            "reason": {
                "type": "string",
                "description": "The reason for the opt-out (optional)."
            }
        },
        "required": ["contact_id", "campaign_id"]
    }
}


# Helper function to register async handlers
def register_async_handler(schema: Dict[str, Any], async_handler: Callable) -> None:
    """Register an async handler function with adapter to make it sync-compatible."""
    
    def sync_adapter(args: Dict[str, Any]) -> str:
        """Adapter to convert async handler to sync for the function registry."""
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(async_handler(args))
        return json.dumps(result)
    
    vb_functions.append(FunctionHandler(schema=schema, handler=sync_adapter))


# Register all the VB System functions
register_async_handler(get_campaign_info_schema, get_campaign_info)
register_async_handler(get_contact_info_schema, get_contact_info)
register_async_handler(get_survey_questions_schema, get_survey_questions)
register_async_handler(save_survey_response_schema, save_survey_response)
register_async_handler(update_subscriber_disposition_schema, update_subscriber_disposition)
register_async_handler(add_contact_opt_out_schema, add_contact_opt_out) 