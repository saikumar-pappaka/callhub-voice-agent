from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request, Response
from typing import Dict, Any
from pathlib import Path

from app.core import handle_call_connection, handle_frontend_connection, functions

# Create router
router = APIRouter()

# Read TwiML template
current_dir = Path(__file__).parent.parent.parent  # Go up two levels to project root
twiml_path = current_dir / "twiml.xml"
twiml_template = twiml_path.read_text(encoding="utf-8")


@router.get("/", response_model=str)
async def root() -> str:
    """Root endpoint that returns server status."""
    return "OpenAI Realtime API with Twilio Demo Server is running. Please visit the web app frontend for the user interface."


@router.get("/public-url")
async def public_url(request: Request) -> Dict[str, str]:
    """Endpoint that returns the public URL."""
    # Get the base URL from request
    base_url = str(request.base_url)
    return {"publicUrl": base_url.rstrip("/")}


@router.get("/tools")
async def tools() -> list:
    """Endpoint that returns available function schemas."""
    return [f.schema for f in functions]


@router.api_route("/twiml", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def twiml(request: Request) -> Response:
    """Endpoint that returns TwiML template with WebSocket URL.
    
    Handles any HTTP method to match the TypeScript implementation.
    """
    # Parse the request base URL and modify for WebSocket
    base_url = str(request.base_url)
    ws_url = base_url.replace("http://", "wss://").replace("https://", "wss://")
    if not ws_url.endswith("/"):
        ws_url += "/"
    ws_url += "call"
    
    # Replace the placeholder
    twiml_content = twiml_template.replace("{{WS_URL}}", ws_url)
    
    # Return as XML
    return Response(content=twiml_content, media_type="text/xml")


@router.websocket("/call")
async def websocket_call(websocket: WebSocket) -> None:
    """WebSocket endpoint for Twilio calls."""
    await websocket.accept()
    try:
        await handle_call_connection(websocket)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Error in Twilio WebSocket: {e}")


@router.websocket("/logs")
async def websocket_logs(websocket: WebSocket) -> None:
    """WebSocket endpoint for frontend logging."""
    await websocket.accept()
    try:
        await handle_frontend_connection(websocket)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Error in frontend WebSocket: {e}") 