# FastAPI WebSocket Server with VB System Integration

A FastAPI-based WebSocket server for OpenAI's Realtime API that integrates with the VB System database. This server provides voice agent capabilities with database integration for campaign management, contact handling, and survey responses.

## Project Structure

```
├── app/
│   ├── api/             # API endpoints
│   ├── core/            # Core functionality
│   ├── db/              # Database access layer
│   ├── models/          # Data models
│   ├── services/        # Business logic services
│   └── utils/           # Utility functions
├── main.py              # Application entry point
├── pyproject.toml       # Project metadata
├── requirements.txt     # Dependencies
└── twiml.xml            # Twilio TwiML template
```

## Features

- WebSocket-based voice agent using OpenAI's Realtime API
- Twilio integration for phone calls
- PostgreSQL database integration via asyncpg
- Layered architecture with separation of concerns:
  - Data access layer (DAOs)
  - Service layer
  - API layer

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with the following variables:
   ```
   PORT=8081
   OPENAI_API_KEY=your_openai_api_key
   VB_DATABASE_URL=postgresql://user:password@host:port/database
   ```

## Running the Server

```
python main.py
```

Or use the entry point defined in pyproject.toml:

```
uvicorn main:app --host 0.0.0.0 --port 8081
```

## API Endpoints

- `/`: Root endpoint with server status
- `/public-url`: Returns the public URL for the server
- `/tools`: Lists available function schemas
- `/twiml`: Returns TwiML template for Twilio integration
- `/call`: WebSocket endpoint for Twilio calls
- `/logs`: WebSocket endpoint for frontend logging

## VB System Integration

The server integrates with VB System database to provide the following functionalities:

1. Campaign Management:
   - Retrieve campaign details
   - Access AI agent configurations

2. Contact Management:
   - Get contact information
   - Handle opt-outs
   - Update contact status

3. Survey Handling:
   - Retrieve survey questions and choices
   - Save survey responses

4. Call Management:
   - Record call dispositions
   - Update subscriber statuses

## Environment Variables

- `PORT`: Server port (default: 8081)
- `OPENAI_API_KEY`: OpenAI API key for Realtime API
- `VB_DATABASE_URL`: PostgreSQL connection URL for VB System

## Dependencies

- fastapi
- uvicorn
- websockets
- asyncpg
- python-dotenv
- pydantic

## Development

To run the server in development mode with auto-reload:

```
python main.py
```

To run tests:

```
pytest
``` 