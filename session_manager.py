import json
import logging
import asyncio
import time
from typing import Dict, Any, Optional, Union
import websockets
from websockets.exceptions import ConnectionClosed
from fastapi import WebSocket
from models import Session, FunctionCallItem
from function_handlers import functions
from constants import SYSTEM_PROMPT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global session instance - Define it at module level
_session = Session()


# Getter and setter functions for session management
def get_session() -> Session:
    """Get the current session."""
    return _session


def reset_session() -> None:
    """Reset the session to a new empty session."""
    global _session
    _session = Session()


def set_openai_api_key(api_key: str) -> None:
    """Set the OpenAI API key for the session.
    
    Args:
        api_key: OpenAI API key
    """
    _session.openai_api_key = api_key


async def handle_call_connection(ws: WebSocket) -> None:
    """Handle Twilio WebSocket connections.
    
    Args:
        ws: The WebSocket connection from Twilio
    """
    # Close existing connection if any
    await cleanup_connection(_session.twilio_conn)
    _session.twilio_conn = ws
    
    try:
        # FastAPI WebSocket receive pattern
        while True:
            try:
                # Try to receive text
                data = await ws.receive_text()
                await handle_twilio_message(data)
            except Exception as e:
                try:
                    # Try to receive bytes
                    data = await ws.receive_bytes()
                    # Handle binary message if needed
                    pass
                except Exception as inner_e:
                    # If both fail, might be a disconnection
                    break
    except Exception as e:
        logger.error(f"Error in Twilio connection: {e}")
    finally:
        await cleanup_connection(_session.model_conn)
        await cleanup_connection(_session.twilio_conn)
        _session.twilio_conn = None
        _session.model_conn = None
        _session.stream_sid = None
        _session.last_assistant_item = None
        _session.response_start_timestamp = None
        _session.latest_media_timestamp = None
        if not _session.frontend_conn:
            # Reset session if no other connections
            reset_session()


async def handle_frontend_connection(ws: WebSocket) -> None:
    """Handle frontend WebSocket connections.
    
    Args:
        ws: The WebSocket connection from the frontend
    """
    # Close existing connection if any
    await cleanup_connection(_session.frontend_conn)
    _session.frontend_conn = ws
    
    try:
        # FastAPI WebSocket receive pattern
        while True:
            try:
                # Try to receive text
                data = await ws.receive_text()
                await handle_frontend_message(data)
            except Exception as e:
                try:
                    # Try to receive bytes
                    data = await ws.receive_bytes()
                    # Handle binary message if needed
                    pass
                except Exception as inner_e:
                    # If both fail, might be a disconnection
                    break
    except Exception as e:
        logger.error(f"Error in frontend connection: {e}")
    finally:
        await cleanup_connection(_session.frontend_conn)
        _session.frontend_conn = None
        if not _session.twilio_conn and not _session.model_conn:
            # Reset session if no other connections
            reset_session()


async def handle_function_call(item: Dict[str, Any]) -> str:
    """Handle function calls from OpenAI.
    
    Args:
        item: Function call data with name and arguments
        
    Returns:
        JSON string with function result
    """
    logger.info(f"Handling function call: {item}")
    
    fn_def = next((f for f in functions if f.schema.name == item.get("name")), None)
    if not fn_def:
        error_msg = f"No handler found for function: {item.get('name')}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})
    
    try:
        args = json.loads(item.get("arguments", "{}"))
    except json.JSONDecodeError:
        return json.dumps({
            "error": "Invalid JSON arguments for function call."
        })
    
    try:
        logger.info(f"Calling function: {fn_def.schema.name} {args}")
        result = await fn_def.handler(args)
        return result
    except Exception as e:
        error_msg = f"Error running function {item.get('name')}: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})


async def handle_twilio_message(data: str) -> None:
    """Handle messages from Twilio WebSocket.
    
    Args:
        data: JSON message from Twilio
    """
    try:
        msg = json.loads(data)
    except json.JSONDecodeError:
        logger.error("Invalid JSON from Twilio")
        return
    
    event_type = msg.get("event")
    
    if event_type == "start":
        _session.stream_sid = msg.get("start", {}).get("streamSid")
        _session.latest_media_timestamp = 0
        _session.last_assistant_item = None
        _session.response_start_timestamp = None
        await try_connect_model()
    
    elif event_type == "media":
        # Ensure timestamp is an integer
        try:
            timestamp = msg.get("media", {}).get("timestamp")
            if timestamp is not None:
                _session.latest_media_timestamp = int(timestamp)
            else:
                _session.latest_media_timestamp = 0
        except (ValueError, TypeError):
            logger.warning(f"Invalid timestamp format: {msg.get('media', {}).get('timestamp')}")
            _session.latest_media_timestamp = 0
            
        if _session.model_conn and _session.model_conn.open:
            await json_send(_session.model_conn, {
                "type": "input_audio_buffer.append",
                "audio": msg.get("media", {}).get("payload")
            })
    elif event_type == "close":
        await close_all_connections()


async def handle_frontend_message(data: str) -> None:
    """Handle messages from frontend WebSocket.
    
    Args:
        data: JSON message from frontend
    """
    try:
        msg = json.loads(data)
    except json.JSONDecodeError:
        logger.error("Invalid JSON from frontend")
        return
    
    if _session.model_conn and _session.model_conn.open:
        await json_send(_session.model_conn, msg)
    
    if msg.get("type") == "session.update":
        _session.saved_config = msg.get("session")


async def try_connect_model() -> None:
    """Try to connect to OpenAI Realtime API."""
    if not _session.twilio_conn or not _session.stream_sid or not _session.openai_api_key:
        return
    
    if _session.model_conn and _session.model_conn.open:
        return
    
    try:
        _session.model_conn = await websockets.connect(
            "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17",
            extra_headers={
                "Authorization": f"Bearer {_session.openai_api_key}",
                "OpenAI-Beta": "realtime=v1",
            }
        )
        
        # Configure the model with complete settings directly in code
        # We're not using frontend config since it's not available
        await json_send(_session.model_conn, {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "turn_detection": {"type": "server_vad"},
                "voice": "ash",
                "input_audio_transcription": {"model": "whisper-1"},
                "input_audio_format": "g711_ulaw",
                "output_audio_format": "g711_ulaw",
                "input_audio_transcription": {
                    "model": "whisper-1",
                    "language": "en"
                },
                "tools": [f.schema.dict() for f in functions],  # Include external functions/tools
                "temperature": 0.5,  # Reduced for more deterministic behavior in speech
                "instructions": SYSTEM_PROMPT,  # Core instruction to the assistant
            }
        })

        
        # Start listener task for model messages
        asyncio.create_task(handle_model_connection())
        
    except Exception as e:
        logger.error(f"Error connecting to OpenAI: {e}")
        await close_model()


async def handle_model_connection() -> None:
    """Handle messages from OpenAI model WebSocket."""
    if not _session.model_conn:
        return
    
    try:
        # Use a standard receive loop instead of async for
        while True:
            if not _session.model_conn or not _session.model_conn.open:
                break
                
            message = await _session.model_conn.recv()
            await handle_model_message(message)
    except ConnectionClosed:
        logger.info("OpenAI model connection closed")
    except Exception as e:
        logger.error(f"Error in model connection: {e}")
    finally:
        await close_model()


async def handle_model_message(data: str) -> None:
    """Handle messages from OpenAI model WebSocket.
    
    Args:
        data: JSON message from OpenAI
    """
    try:
        event = json.loads(data)
    except json.JSONDecodeError:
        logger.error("Invalid JSON from OpenAI")
        return
    
    # Forward to frontend for logging
    if _session.frontend_conn:
        try:
            await json_send(_session.frontend_conn, event)
        except Exception as e:
            logger.error(f"Error sending to frontend: {e}")
    
    event_type = event.get("type")
    
    if event_type == "input_audio_buffer.speech_started":
        await handle_truncation()
    
    elif event_type == "response.audio.delta":
        if _session.twilio_conn and _session.stream_sid:
            if _session.response_start_timestamp is None:
                _session.response_start_timestamp = _session.latest_media_timestamp or 0
            
            if event.get("item_id"):
                _session.last_assistant_item = event.get("item_id")
            await json_send(_session.twilio_conn, {
                "event": "media",
                "streamSid": _session.stream_sid,
                "media": {"payload": event.get("delta")}
            })
            await json_send(_session.twilio_conn, {
                "event": "mark",
                "streamSid": _session.stream_sid
            })
    elif event_type == "response.output_item.done":
        item = event.get("item", {})
        if item.get("type") == "function_call":
            try:
                output = await handle_function_call(item)
                
                if _session.model_conn and _session.model_conn.open:
                    await json_send(_session.model_conn, {
                        "type": "conversation.item.create",
                        "item": {
                            "type": "function_call_output",
                            "call_id": item.get("call_id"),
                            "output": output
                        }
                    })
                    
                    await json_send(_session.model_conn, {
                        "type": "response.create"
                    })
            except Exception as e:
                logger.error(f"Error handling function call: {e}")


async def handle_truncation() -> None:
    """Handle audio truncation when user starts speaking."""
    if not _session.last_assistant_item or _session.response_start_timestamp is None:
        return
    
    try:
        # Ensure both timestamps are integers for subtraction
        latest = 0 if _session.latest_media_timestamp is None else int(_session.latest_media_timestamp)
        start = 0 if _session.response_start_timestamp is None else int(_session.response_start_timestamp)
        
        elapsed_ms = latest - start
        audio_end_ms = elapsed_ms if elapsed_ms > 0 else 0
        
        if _session.model_conn and _session.model_conn.open:
            await json_send(_session.model_conn, {
                "type": "conversation.item.truncate",
                "item_id": _session.last_assistant_item,
                "content_index": 0,
                "audio_end_ms": audio_end_ms
            })
        
        if _session.twilio_conn and _session.stream_sid:
            await json_send(_session.twilio_conn, {
                "event": "clear",
                "streamSid": _session.stream_sid
            })
        
        _session.last_assistant_item = None
        _session.response_start_timestamp = None
    except Exception as e:
        logger.error(f"Error in handle_truncation: {e}")
        _session.last_assistant_item = None
        _session.response_start_timestamp = None


async def close_model() -> None:
    """Close the OpenAI model connection."""
    await cleanup_connection(_session.model_conn)
    _session.model_conn = None
    
    if not _session.twilio_conn and not _session.frontend_conn:
        reset_session()


async def close_all_connections() -> None:
    """Close all active connections."""
    await cleanup_connection(_session.twilio_conn)
    await cleanup_connection(_session.model_conn)
    await cleanup_connection(_session.frontend_conn)


async def cleanup_connection(ws: Optional[Union[WebSocket, websockets.WebSocketClientProtocol]]) -> None:
    """Safely close a WebSocket connection.
    
    Args:
        ws: WebSocket connection to close
    """
    if not ws:
        return
    
    try:
        # Check if the websocket is still open before closing
        if isinstance(ws, WebSocket):
            # For FastAPI WebSockets
            if ws.client_state.name == "CONNECTED":
                await ws.close()
        else:
            # For websockets.WebSocketClientProtocol
            if ws.open:
                await ws.close()
    except Exception as e:
        logger.error(f"Error closing WebSocket: {e}")


async def json_send(ws: Optional[Union[WebSocket, websockets.WebSocketClientProtocol]], obj: Any) -> None:
    """Send a JSON object over WebSocket.
    
    Args:
        ws: WebSocket connection
        obj: Object to send as JSON
    """
    if not ws:
        return
    
    try:
        if isinstance(ws, WebSocket):
            await ws.send_text(json.dumps(obj))
        else:
            await ws.send(json.dumps(obj))
    except Exception as e:
        logger.error(f"Error sending message: {e}")
