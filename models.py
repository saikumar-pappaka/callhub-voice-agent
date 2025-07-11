from typing import Optional, Dict, List, Any, Callable, Awaitable, Union
from pydantic import BaseModel, Field
import websockets
from fastapi import WebSocket


class FunctionParameter(BaseModel):
    type: str
    description: Optional[str] = None


class FunctionParameters(BaseModel):
    type: str
    properties: Dict[str, FunctionParameter]
    required: List[str]


class FunctionSchema(BaseModel):
    name: str
    type: str = "function"
    description: Optional[str] = None
    parameters: FunctionParameters


class FunctionCallItem(BaseModel):
    name: str
    arguments: str
    call_id: Optional[str] = None


class Session:
    """Session model for managing connections and state.
    
    Not a Pydantic model because it contains WebSocket connections
    which cannot be serialized.
    """
    twilio_conn: Optional[WebSocket] = None
    frontend_conn: Optional[WebSocket] = None
    model_conn: Optional[websockets.WebSocketClientProtocol] = None
    stream_sid: Optional[str] = None
    saved_config: Optional[Any] = None
    last_assistant_item: Optional[str] = None
    response_start_timestamp: Optional[int] = None
    latest_media_timestamp: Optional[int] = None
    openai_api_key: Optional[str] = None


class TwilioStartMessage(BaseModel):
    event: str = "start"
    start: Dict[str, str]


class TwilioMediaMessage(BaseModel):
    event: str = "media"
    streamSid: str
    media: Dict[str, Any]


class TwilioCloseMessage(BaseModel):
    event: str = "close"
    streamSid: str


# Type aliases for function handlers
FunctionHandlerType = Callable[[Any], Awaitable[str]]


class FunctionHandler:
    """Class for storing function schema and handler.
    
    Not a Pydantic model because it contains a callable
    which cannot be serialized.
    """
    schema: FunctionSchema
    handler: FunctionHandlerType

    def __init__(self, schema: FunctionSchema, handler: FunctionHandlerType):
        self.schema = schema
        self.handler = handler 