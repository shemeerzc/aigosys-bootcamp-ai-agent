# ============================================================
# Campus agent powered by Groq (OpenAI-compatible API)
# Local / teaching use only — same tools as agent.py
# Run: python agent_groq.py
# ============================================================

# Import json — parse tool argument JSON from the model
import json
# Import os — read GROQ_API_KEY / GROQ_MODEL from environment
import os

# Import load_dotenv — load values from .env file
from dotenv import load_dotenv
# Import OpenAI client — Groq supports the same client interface
from openai import OpenAI

# Import init_db — prepare SQLite tables
from db import init_db
# Import tool functions (same as OpenAI agent)
from tools import (
    add_event,
    college_faq,
    create_reminder,
    generate_certificate,
    list_reminders,
    search_events,
)

# Load .env into environment variables
load_dotenv()

# Create client pointed at Groq's OpenAI-compatible endpoint
client = OpenAI(
    # API key from https://console.groq.com
    api_key=os.getenv("GROQ_API_KEY"),
    # Groq base URL (this is the main difference from OpenAI)
    base_url="https://api.groq.com/openai/v1",
)

# Model name (override in .env with GROQ_MODEL=...)
# Default is a widely available Groq model that supports tools
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# TOOLS schema — same tool list as agent.py (tells Groq what it can call)
TOOLS = [
    # Tool: search campus events
    {
        "type": "function",
        "function": {
            "name": "search_events",
            "description": "Search college events by keyword (AI, coding, placement, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keyword to search in event title or location",
                    }
                },
                "required": ["query"],
            },
        },
    },
    # Tool: create a reminder
    {
        "type": "function",
        "function": {
            "name": "create_reminder",
            "description": "Save a reminder for the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Reminder text to save",
                    }
                },
                "required": ["text"],
            },
        },
    },
    # Tool: list reminders
    {
        "type": "function",
        "function": {
            "name": "list_reminders",
            "description": "List all saved reminders",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    # Tool: add a new event
    {
        "type": "function",
        "function": {
            "name": "add_event",
            "description": "Add a new college event to the database",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title"},
                    "date": {
                        "type": "string",
                        "description": "Event date, e.g. 2026-10-08",
                    },
                    "location": {"type": "string", "description": "Event venue"},
                },
                "required": ["title", "date", "location"],
            },
        },
    },
    # Tool: campus FAQ
    {
        "type": "function",
        "function": {
            "name": "college_faq",
            "description": (
                "Answer campus FAQ: library, wifi, bus, hostel, placement, canteen"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "FAQ topic, e.g. library, wifi, bus",
                    }
                },
                "required": ["topic"],
            },
        },
    },
    # Tool: generate certificate via pdf-app API
    {
        "type": "function",
        "function": {
            "name": "generate_certificate",
            "description": (
                "Generate a completion certificate PDF for a student name "
                "using the certificate API, and return preview/share links"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Student full name for the certificate",
                    }
                },
                "required": ["name"],
            },
        },
    },
]


def call_tool(name, arguments):
    """Map tool name → real Python function."""
    # Run search_events
    if name == "search_events":
        return search_events(arguments["query"])
    # Run create_reminder
    if name == "create_reminder":
        return create_reminder(arguments["text"])
    # Run list_reminders
    if name == "list_reminders":
        return list_reminders()
    # Run add_event
    if name == "add_event":
        return add_event(arguments["title"], arguments["date"], arguments["location"])
    # Run college_faq
    if name == "college_faq":
        return college_faq(arguments["topic"])
    # Run generate_certificate
    if name == "generate_certificate":
        return generate_certificate(arguments["name"])
    # Unknown tool
    return f"Unknown tool: {name}"


def stream_agent(user_message):
    """
    Groq streaming agent loop (same event shape as OpenAI agent).
    Yields: delta / tool_call / tool_result / done
    """
    # Build starting messages (system + user)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful campus assistant. "
                "Use tools for events, reminders, FAQ, and certificates when needed."
            ),
        },
        {"role": "user", "content": user_message},
    ]

    # Keep calling Groq until we get a final text-only answer
    while True:
        # Create a streaming chat completion on Groq
        stream = client.chat.completions.create(
            # Which Groq model to use
            model=GROQ_MODEL,
            # Conversation history
            messages=messages,
            # Available tools
            tools=TOOLS,
            # Stream tokens live
            stream=True,
        )

        # Accumulate assistant text
        full_text = ""
        # Accumulate tool-call fragments by index
        collected_tools = {}

        # Read each streamed chunk
        for chunk in stream:
            # Some chunks may have empty choices — skip them
            if not chunk.choices:
                continue
            # New content in this chunk
            delta = chunk.choices[0].delta

            # Stream normal text
            if delta.content:
                full_text += delta.content
                yield {"type": "delta", "text": delta.content}

            # Collect tool-call pieces
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    i = tc.index
                    if i not in collected_tools:
                        collected_tools[i] = {
                            "id": "",
                            "name": "",
                            "arguments": "",
                        }
                    if tc.id:
                        collected_tools[i]["id"] = tc.id
                    if tc.function and tc.function.name:
                        collected_tools[i]["name"] = tc.function.name
                    if tc.function and tc.function.arguments:
                        collected_tools[i]["arguments"] += tc.function.arguments

        # No tools → finished
        if not collected_tools:
            yield {"type": "done"}
            return

        # Groq sometimes omits tool id in stream — fill a placeholder
        for i, t in collected_tools.items():
            if not t["id"]:
                t["id"] = f"call_{i}"

        # Append assistant tool request to history
        messages.append(
            {
                "role": "assistant",
                "content": full_text or None,
                "tool_calls": [
                    {
                        "id": t["id"],
                        "type": "function",
                        "function": {
                            "name": t["name"],
                            "arguments": t["arguments"],
                        },
                    }
                    for t in collected_tools.values()
                ],
            }
        )

        # Execute each tool and append results
        for t in collected_tools.values():
            name = t["name"]
            # Empty args string → use {}
            args = json.loads(t["arguments"] or "{}")
            yield {"type": "tool_call", "name": name, "args": args}

            result = call_tool(name, args)
            yield {"type": "tool_result", "result": str(result)}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": t["id"],
                    "content": str(result),
                }
            )


def run_agent(user_message):
    """Print Groq agent stream in the terminal."""
    print("Agent (Groq): ", end="", flush=True)
    for event in stream_agent(user_message):
        if event["type"] == "delta":
            print(event["text"], end="", flush=True)
        elif event["type"] == "tool_call":
            print(f"\nTool call: {event['name']}({event['args']})")
            print("Agent (Groq): ", end="", flush=True)
        elif event["type"] == "tool_result":
            print(f"Tool result: {event['result']}")
        elif event["type"] == "done":
            print()


# Runs only for: python agent_groq.py
if __name__ == "__main__":
    # Stop early if Groq key is missing
    if not os.getenv("GROQ_API_KEY"):
        print("Missing GROQ_API_KEY in .env — get one from https://console.groq.com")
        raise SystemExit(1)

    # Prepare database
    init_db()
    # Show which model is active
    print(f"Using Groq model: {GROQ_MODEL}")
    print("Local only. Type quit to exit.\n")

    # Terminal chat loop
    while True:
        user = input("You: ").strip()
        if user.lower() in ("quit", "exit"):
            break
        run_agent(user)
        print()
