import json
from pathlib import Path
from datetime import datetime

LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

LEADS_LOG = LOGS_DIR / "leads.jsonl"
FEEDBACK_LOG = LOGS_DIR / "feedback.jsonl"


def record_customer_interest(email: str, name: str, message: str) -> str:
    entry = {
        "type": "lead",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "email": email,
        "name": name,
        "message": message,
    }
    with LEADS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return f"Thanks, {name}! We’ve recorded your interest. We’ll reach out at {email}."


def record_feedback(question: str) -> str:
    entry = {
        "type": "feedback",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "question": question,
    }
    with FEEDBACK_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return "Thanks! I’ve noted that for the team and will follow up."


# Tool specifications for OpenAI tool-calling
openai_tools = [
    {
        "type": "function",
        "function": {
            "name": "record_customer_interest",
            "description": "Record a potential customer’s contact details and message for follow-up.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Customer email"},
                    "name": {"type": "string", "description": "Customer name"},
                    "message": {"type": "string", "description": "A short note about their interest"},
                },
                "required": ["email", "name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_feedback",
            "description": "Log customer feedback or an unanswered question so a human can respond.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The feedback or unanswered question"},
                },
                "required": ["question"],
            },
        },
    },
]

