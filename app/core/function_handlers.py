from typing import Dict, Any, List

from app.models import FunctionHandler
from app.core.vb_function_handlers import vb_functions

# Function registry
functions: List[FunctionHandler] = []

# Define the handler for note_question_answers
def note_question_answers(args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        question_id = args["question_id"]  # Now a tuple/array [id, question_text]
        answer = args["answer"]  # Now a tuple/array [id, answer_text]
        voter_id = args.get("voter_id")

        # Extract components - handle both array format and direct string format for backward compatibility
        if isinstance(question_id, list) and len(question_id) >= 2:
            question_id_value, question_text = question_id
        else:
            question_id_value = question_id
            question_text = str(question_id)

        if isinstance(answer, list) and len(answer) >= 2:
            answer_id_value, answer_text = answer
        else:
            answer_id_value = answer
            answer_text = str(answer)

        # Simulate storing the answer (e.g., log, write to DB, etc.)
        print(f"[Note] Voter ID: {voter_id}")
        print(f"Question ID: {question_id_value}, Text: {question_text}")
        print(f"Answer ID: {answer_id_value}, Text: {answer_text}")

        # Return acknowledgment
        return {
            "status": "noted",
            "question": {
                "id": question_id_value,
                "text": question_text
            },
            "answer": {
                "id": answer_id_value,
                "text": answer_text
            }
        }
    except Exception as e:
        print(f"Error in note_question_answers: {e}")
        print(f"Raw args: {args}")
        # Return a generic response for robustness
        return {
            "status": "error",
            "message": f"Failed to process answer: {str(e)}",
            "args_received": args
        }


# Schema for note_question_answers
note_question_answers_schema = {
    "name": "note_question_answers",
    "type": "function",
    "description": "Record a voter's answer to a survey question.",
    "parameters": {
        "type": "object",
        "properties": {
            "question_id": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 2,
                "maxItems": 2,
                "description": "A tuple containing [id, question_text] for the question being answered."
            },
            "answer": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "minItems": 2,
                "maxItems": 2,
                "description": "A tuple containing [id, answer_text] for the answer provided by the voter."
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

# Add VB System functions to the registry
functions.extend(vb_functions) 