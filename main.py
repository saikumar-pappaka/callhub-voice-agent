import os
import logging
from typing import Dict, Any
from pathlib import Path
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import PlainTextResponse

from session_manager import handle_call_connection, handle_frontend_connection, set_openai_api_key
from function_handlers import functions

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get environment variables
PORT = int(os.getenv("PORT", "8081"))
PUBLIC_URL = os.getenv("PUBLIC_URL", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Check required environment variables
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is required")
    exit(1)

# Set the OpenAI API key for the session
set_openai_api_key(OPENAI_API_KEY)

# Create FastAPI app
app = FastAPI(
    title="OpenAI Realtime API with Twilio Demo Server",
    description="Python FastAPI implementation of the TypeScript WebSocket server for OpenAI Realtime API with Twilioooo TESSST",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Read TwiML template
current_dir = Path(__file__).parent
twiml_path = current_dir / "twiml.xml"
twiml_template = twiml_path.read_text(encoding="utf-8")


@app.get("/", response_class=PlainTextResponse)
async def root() -> str:
    """Root endpoint that returns server status."""
    return "OpenAI Realtime API with Twilio Demo Server is running. Please visit the web app frontend for the user interface."


@app.get("/public-url")
async def public_url() -> Dict[str, str]:
    """Endpoint that returns the public URL."""
    return {"publicUrl": PUBLIC_URL}


@app.get("/tools")
async def tools() -> list:
    """Endpoint that returns available function schemas."""
    return [f.schema for f in functions]


@app.api_route("/twiml", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"])
async def twiml(request: Request) -> Response:
    """Endpoint that returns TwiML template with WebSocket URL.
    
    Handles any HTTP method to match the TypeScript implementation.
    """
    # Parse the PUBLIC_URL and modify for WebSocket
    ws_url = PUBLIC_URL.replace("http://", "wss://").replace("https://", "wss://")
    if not ws_url.endswith("/"):
        ws_url += "/"
    ws_url += "call"
    
    # Replace the placeholder
    twiml_content = twiml_template.replace("{{WS_URL}}", ws_url)
    
    # Return as XML
    return Response(content=twiml_content, media_type="text/xml")


@app.websocket("/call")
async def websocket_call(websocket: WebSocket) -> None:
    """WebSocket endpoint for Twilio calls."""
    await websocket.accept()
    logger.info("New Twilio WebSocket connection")
    try:
        await handle_call_connection(websocket)
    except WebSocketDisconnect:
        logger.info("Twilio WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in Twilio WebSocket: {e}")


@app.websocket("/logs")
async def websocket_logs(websocket: WebSocket) -> None:
    """WebSocket endpoint for frontend logging."""
    await websocket.accept()
    logger.info("New frontend WebSocket connection")
    try:
        await handle_frontend_connection(websocket)
    except WebSocketDisconnect:
        logger.info("Frontend WebSocket disconnected")
    except Exception as e:
        logger.error(f"Error in frontend WebSocket: {e}")


def run_server() -> None:
    """Entry point for the script defined in pyproject.toml."""
    import uvicorn
    # Explicitly bind to IPv4 only
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)


if __name__ == "__main__":
    import uvicorn
    # Explicitly bind to IPv4 only and disable IPv6
    import socket
    socket.AF_INET = socket.AF_INET  # Force IPv4
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True) 