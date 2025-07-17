import os
import logging
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router
from app.core import set_openai_api_key

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get environment variables
PORT = int(os.getenv("PORT", "8081"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
VB_DATABASE_URL = os.getenv("VB_DATABASE_URL", "")

# Check required environment variables
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable is required")
    exit(1)

if not VB_DATABASE_URL:
    logger.warning("VB_DATABASE_URL environment variable is not set. VB System functions will not work.")
# Set the OpenAI API key for the session
set_openai_api_key(OPENAI_API_KEY)

# Create FastAPI app
app = FastAPI(
    title="OpenAI Realtime API with VB System Integration",
    description="FastAPI implementation of WebSocket server for OpenAI Realtime API with VB System database integration",
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

# Include API router
app.include_router(router)


def run_server() -> None:
    """Entry point for the script defined in pyproject.toml."""
    import uvicorn
    # Explicitly bind to IPv4 only
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)


if __name__ == "__main__":
    import uvicorn
    import socket
    # Explicitly bind to IPv4 only and disable IPv6
    socket.AF_INET6 = socket.AF_INET  # Force IPv4
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True) 