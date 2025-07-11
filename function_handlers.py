import json
from typing import List, Any
import httpx
from models import FunctionSchema, FunctionParameters, FunctionParameter, FunctionHandler


# List to store function handlers
functions: List[FunctionHandler] = []


# Weather function schema
weather_schema = FunctionSchema(
    name="get_weather_from_coords",
    type="function",
    description="Get the current weather",
    parameters=FunctionParameters(
        type="object",
        properties={
            "latitude": FunctionParameter(type="number"),
            "longitude": FunctionParameter(type="number"),
        },
        required=["latitude", "longitude"],
    ),
)
 