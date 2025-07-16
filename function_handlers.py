from typing import Dict, Any, List, Callable

# Base FunctionHandler class (if not already defined)
class FunctionHandler:
    def __init__(self, schema: Dict[str, Any], handler: Callable[[Dict[str, Any]], Any]):
        self.schema = schema
        self.handler = handler

# Function registry
functions: List[FunctionHandler] = []

# Define the handler for note_question_answers
def note_question_answers(args: Dict[str, Any]) -> str:
    question_id = args["question_id"]
    answer = args["answer"]
    voter_id = args.get("voter_id")

    # Simulate storing the answer (e.g., log, write to DB, etc.)
    print(f"[Note] Voter ID: {voter_id}, Question: {question_id}, Answer: {answer}")

    # Return acknowledgment
    return {"status": "noted", "question_id": question_id}


# Schema for note_question_answers
note_question_answers_schema = {
    "name": "note_question_answers",
    "type": "function",
    "description": "Record a voter's answer to a survey question.",
    "parameters": {
        "type": "object",
        "properties": {
            "question_id": {
                "type": "string",
                "description": "The ID of the question being answered."
            },
            "answer": {
                "type": "string",
                "description": "The answer or response provided by the voter."
            },
            "voter_id": {
                "type": "string",
                "description": "Optional voter ID for tracking answers per user."
            }
        },
        "required": ["question_id", "answer"]
    },
}

# Register the function
functions.append(FunctionHandler(
    schema=note_question_answers_schema,
    handler=note_question_answers
))
