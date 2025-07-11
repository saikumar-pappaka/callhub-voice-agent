# FastAPI OpenAI Realtime WebSocket Server for Twilio

This is a Python FastAPI implementation of the TypeScript WebSocket server that bridges between Twilio phone calls and OpenAI's Realtime API. It maintains API compatibility with the original TypeScript version.

## Features

- **WebSocket Server**: Handles both Twilio and frontend connections
- **OpenAI Realtime API Integration**: Streams audio between Twilio and OpenAI
- **Function Calling**: Supports OpenAI function calling with extensible handlers
- **Session Management**: Maintains state across WebSocket connections
- **TwiML Support**: Generates TwiML responses for Twilio

## Requirements

- Python 3.8+
- OpenAI API key with access to the Realtime API
- Publicly accessible URL (for Twilio integration)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd fastapi-websocket-server
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit the `.env` file to add your OpenAI API key and public URL.

## Usage

### Starting the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8081
```

Or use the Python script directly:

```bash
python main.py
```

### Endpoints

- **GET `/`**: Server status information
- **GET `/public-url`**: Returns configured public URL
- **GET `/tools`**: Lists available function schemas
- **ALL `/twiml`**: Returns TwiML template with WebSocket URL

### WebSocket Endpoints

- **WebSocket `/call`**: For Twilio Stream connections
- **WebSocket `/logs`**: For frontend logging and configuration

## Architecture

The server uses a modular architecture with the following components:

- **main.py**: FastAPI application with HTTP and WebSocket endpoints
- **session_manager.py**: Manages WebSocket connections and message routing
- **function_handlers.py**: Implements function calling mechanisms
- **models.py**: Defines data models and validation using Pydantic

## Function Calling

To add new functions that can be called from OpenAI:

1. Define a function schema in `function_handlers.py`
2. Implement a handler function that returns a JSON string
3. Register the function in the `functions` list

Example:

```python
# Define schema
new_function_schema = FunctionSchema(
    name="my_function",
    type="function",
    description="Does something useful",
    parameters=FunctionParameters(
        type="object",
        properties={
            "param1": FunctionParameter(type="string"),
        },
        required=["param1"],
    ),
)

# Implement handler
async def my_function_handler(args: Any) -> str:
    result = {"result": args.get("param1")}
    return json.dumps(result)

# Register function
functions.append(FunctionHandler(schema=new_function_schema, handler=my_function_handler))
```

## Deployment

The server can be deployed on any platform that supports Python and WebSockets. For production:

1. Use a production ASGI server like Uvicorn behind Nginx
2. Set up SSL certificates for secure WebSocket connections
3. Configure environment variables for production settings
4. Use a process manager like Supervisor or systemd

## Compatibility

This server maintains API compatibility with the original TypeScript implementation, allowing it to work with the existing frontend and Twilio integration. 