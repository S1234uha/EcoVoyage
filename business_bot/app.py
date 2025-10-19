import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re

from dotenv import load_dotenv
from pdfminer.high_level import extract_text
import gradio as gr

from openai import OpenAI
import google.generativeai as genai
from google.api_core.exceptions import NotFound, PermissionDenied, FailedPrecondition

from .tools import (
    record_customer_interest,
    record_feedback,
    openai_tools,
)


ROOT = Path(__file__).parent
SUMMARY_PATH = ROOT / "business_summary.txt"
PDF_PATH = ROOT / "about_business.pdf"


def load_context() -> Dict[str, str]:
    summary = SUMMARY_PATH.read_text(encoding="utf-8") if SUMMARY_PATH.exists() else ""
    pdf_text = extract_text(str(PDF_PATH)) if PDF_PATH.exists() else ""
    return {"summary": summary, "pdf": pdf_text}


SYSTEM_PROMPT = (
    "You are EcoVoyage Travel’s virtual concierge. Stay in character as a helpful,"
    " sustainability-first travel advisor. Use the provided business summary and PDF"
    " to answer questions accurately. If you cannot confidently answer, call the"
    " record_feedback tool with the user’s question. Encourage potential customers"
    " to share their name and email, and call record_customer_interest when they do."
)


def make_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set. Put it in a .env file.")
    return OpenAI(api_key=api_key)


def chat_openai(messages: List[Dict[str, str]], tools: List[Dict[str, Any]], model: str) -> Dict[str, Any]:
    client = make_openai_client()

    while True:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=0.5,
        )

        msg = resp.choices[0].message

        if msg.tool_calls:
            # Important: include the assistant message that invoked tools
            # so the following tool messages have a valid preceding tool_calls.
            assistant_tool_calls = []
            for tc in msg.tool_calls:
                assistant_tool_calls.append({
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })

            messages.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": assistant_tool_calls,
            })

            for tc in msg.tool_calls:
                fn = tc.function
                name = fn.name
                args = fn.arguments  # JSON string per SDK
                import json

                try:
                    parsed = json.loads(args) if isinstance(args, str) else (args or {})
                except Exception:
                    parsed = {}

                tool_result = ""
                if name == "record_customer_interest":
                    tool_result = record_customer_interest(
                        email=parsed.get("email", ""),
                        name=parsed.get("name", ""),
                        message=parsed.get("message", ""),
                    )
                elif name == "record_feedback":
                    tool_result = record_feedback(question=parsed.get("question", ""))
                else:
                    tool_result = f"Unknown tool: {name}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": name,
                    "content": tool_result,
                })
            # Continue the loop: the tool outputs are now in messages
            continue
        else:
            # Return the model’s direct answer
            return {"answer": msg.content}


def to_gemini_function_declarations(openai_tools_spec: List[Dict[str, Any]]):
    fns = []
    for t in openai_tools_spec:
        f = t.get("function", {}) if isinstance(t, dict) else {}
        if not f:
            continue
        fns.append(
            {
                "name": f.get("name"),
                "description": f.get("description", ""),
                # Gemini accepts JSON Schema-like parameter specs
                "parameters": f.get("parameters", {"type": "object", "properties": {}}),
            }
        )
    return [{"function_declarations": fns}] if fns else []


def chat_gemini(messages: List[Dict[str, str]], tools: List[Dict[str, Any]], model: str) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set. Put it in a .env file.")
    genai.configure(api_key=api_key)

    # Combine system messages into a single system instruction
    system_msgs = [m.get("content", "") for m in messages if m.get("role") == "system"]
    system_instruction = "\n\n".join(system_msgs)

    # Build chat history from user/assistant messages
    history = []
    for m in messages:
        role = m.get("role")
        if role in ("user", "assistant"):
            history.append({"role": role, "parts": [m.get("content", "")]})

    gemini_tools = to_gemini_function_declarations(tools)
    def make_chat(model_name: str):
        mo = genai.GenerativeModel(model_name=model_name, tools=gemini_tools, system_instruction=system_instruction)
        return mo.start_chat(history=history[:-1] if history else [])

    chat = make_chat(model)
    last_user = history[-1]["parts"][0] if history else ""

    while True:
        try:
            resp = chat.send_message(last_user)
        except NotFound:
            alt = model if model.endswith("-latest") else f"{model}-latest"
            try:
                chat = make_chat(alt)
                resp = chat.send_message(last_user)
            except Exception as e:
                return {"answer": (
                    f"Gemini model '{model}' not found. Try setting MODEL to '{alt}' or another available model (e.g., 'gemini-1.5-pro-latest')."
                )}
        except (PermissionDenied, FailedPrecondition) as e:
            return {"answer": (
                "Gemini access issue. Check GEMINI_API_KEY permissions and model availability in your region/account."
            )}
        except Exception as e:
            return {"answer": f"Gemini error: {e}"}

        # Check for function calls in response parts
        called = False
        for cand in getattr(resp, "candidates", []) or []:
            parts = getattr(getattr(cand, "content", None), "parts", []) or []
            for part in parts:
                fc = getattr(part, "function_call", None)
                if fc:
                    name = getattr(fc, "name", "")
                    args = getattr(fc, "args", {}) or {}

                    if name == "record_customer_interest":
                        tool_result = record_customer_interest(
                            email=args.get("email", ""),
                            name=args.get("name", ""),
                            message=args.get("message", ""),
                        )
                    elif name == "record_feedback":
                        tool_result = record_feedback(question=args.get("question", ""))
                    else:
                        tool_result = f"Unknown tool: {name}"

                    chat.send_message({
                        "role": "tool",
                        "parts": [
                            {
                                "functionResponse": {
                                    "name": name,
                                    "response": {"result": tool_result},
                                }
                            }
                        ],
                    })
                    called = True
        if called:
            last_user = ""
            continue

        return {"answer": getattr(resp, "text", "").strip()}


def build_initial_messages(context: Dict[str, str]) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": (
                "Business summary (trusted context):\n" + context.get("summary", "") +
                "\n\nBusiness PDF (trusted context):\n" + context.get("pdf", "")
            ),
        },
    ]


def gradio_chat(user_input: str, history: List[List[str]]):
    load_dotenv()
    provider = (os.getenv("PROVIDER") or "openai").lower()
    # Defaults per provider
    if provider == "gemini":
        model = os.getenv("MODEL") or "gemini-1.5-flash-latest"
    else:
        model = os.getenv("MODEL") or "gpt-4o-mini"

    # Deterministic lead capture pre-check (helps on Spaces if model skips tools)
    def parse_lead(text: str) -> Optional[Tuple[str, str, str]]:
        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        if not email_match:
            return None
        email = email_match.group(0)
        name = ""
        # Simple name heuristics
        name_match = re.search(r"\b(?:I am|I'm|My name is)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)", text)
        if name_match:
            name = name_match.group(1).strip()
        message = text.strip()
        return email, name, message

    context = load_context()
    messages: List[Dict[str, str]] = build_initial_messages(context)

    # Map the Gradio history into the message list
    for user_msg, assistant_msg in history:
        if user_msg:
            messages.append({"role": "user", "content": user_msg})
        if assistant_msg:
            messages.append({"role": "assistant", "content": assistant_msg})

    # If the user likely provided contact details, capture the lead immediately
    lead = parse_lead(user_input)
    if lead:
        email, name, msg = lead
        confirmation = record_customer_interest(email=email, name=name, message=msg)
        followup = (
            " If you have preferred dates, budget per traveler, pace, or lodging style,"
            " share them and I’ll tailor options."
        )
        return confirmation + followup

    messages.append({"role": "user", "content": user_input})

    if provider == "openai":
        result = chat_openai(messages, openai_tools, model)
        return result["answer"]
    elif provider == "gemini":
        result = chat_gemini(messages, openai_tools, model)
        return result["answer"]
    else:
        return "Unsupported PROVIDER. Use 'openai' or 'gemini'."


def main():
    load_dotenv()
    iface = gr.ChatInterface(
        fn=gradio_chat,
        title="EcoVoyage Travel Concierge",
        description=(
            "Ask about trips, sustainability, or request a custom itinerary."
            " Share your name and email to plan your next eco-adventure!"
        ),
    )
    iface.launch()


if __name__ == "__main__":
    main()
