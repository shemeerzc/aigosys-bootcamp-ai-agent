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
    # ---- tool 1: search_events ----
    {
        # Groq tool type (always "function" for tool calling)
        "type": "function",
        "function": {
            # Must match call_tool() name below
            "name": "search_events",
            # Helps Groq know when to use this tool
            "description": (
                "Search college events. Use empty query or 'all' for every event. "
                "For one event pass main keywords only (e.g. cyber, workshop, AI)."
            ),
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
    # ---- tool 2: create_reminder ----
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
    # ---- tool 3: list_reminders ----
    {
        "type": "function",
        "function": {
            "name": "list_reminders",
            "description": "List all saved reminders",
            # No arguments needed
            "parameters": {"type": "object", "properties": {}},
        },
    },
    # ---- tool 4: add_event ----
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
    # ---- tool 5: college_faq ----
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
    # ---- tool 6: generate_certificate ----
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
            # system = rules for Groq model
            "role": "system",
            "content": (
                "You are a helpful campus assistant. "
                "Use tools for events, reminders, FAQ, and certificates when needed."
            ),
        },
        # user = student question
        {"role": "user", "content": user_message},
    ]

    # Keep calling Groq until we get a final text-only answer
    while True:
        # Create a streaming chat completion on Groq
        stream = client.chat.completions.create(
            # Which Groq model to use (from .env)
            model=GROQ_MODEL,
            # Full conversation history
            messages=messages,
            # Tell Groq which tools exist
            tools=TOOLS,
            # stream=True → print answer live
            stream=True,
        )

        # Accumulate assistant text from all chunks
        full_text = ""
        # Accumulate tool-call fragments by index
        collected_tools = {}

        # Read each streamed chunk from Groq
        for chunk in stream:
            # Some chunks may have empty choices — skip them
            if not chunk.choices:
                continue
            # New content in this chunk
            delta = chunk.choices[0].delta

            # If chunk has normal text, stream it out
            if delta.content:
                full_text += delta.content
                yield {"type": "delta", "text": delta.content}

            # If chunk has tool-call pieces, collect them
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    # index groups pieces of the same tool call
                    i = tc.index
                    # First time seeing this index → create empty slot
                    if i not in collected_tools:
                        collected_tools[i] = {
                            "id": "",
                            "name": "",
                            "arguments": "",
                        }
                    # Save tool call id when it arrives
                    if tc.id:
                        collected_tools[i]["id"] = tc.id
                    # Save function name when it arrives
                    if tc.function and tc.function.name:
                        collected_tools[i]["name"] = tc.function.name
                    # Arguments arrive in pieces — append them
                    if tc.function and tc.function.arguments:
                        collected_tools[i]["arguments"] += tc.function.arguments

        # No tools requested → final answer is done
        if not collected_tools:
            yield {"type": "done"}
            return

        # Groq sometimes omits tool id in stream — fill a placeholder
        for i, t in collected_tools.items():
            if not t["id"]:
                t["id"] = f"call_{i}"

        # Save assistant tool request into chat history
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

        # Run each requested tool in Python
        for t in collected_tools.values():
            # Tool function name
            name = t["name"]
            # Parse JSON args (empty string → {})
            args = json.loads(t["arguments"] or "{}")
            # Tell CLI/API which tool is running
            yield {"type": "tool_call", "name": name, "args": args}

            # Execute real Python tool
            result = call_tool(name, args)
            # Send tool output to CLI/API
            yield {"type": "tool_result", "result": str(result)}

            # Add tool result back for next Groq call
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": t["id"],
                    "content": str(result),
                }
            )


def run_agent(user_message):
    """Print Groq agent stream in the terminal."""
    # Print prefix before streamed text
    print("Agent (Groq): ", end="", flush=True)
    # Consume every event from stream_agent
    for event in stream_agent(user_message):
        # Normal answer text piece
        if event["type"] == "delta":
            print(event["text"], end="", flush=True)
        # Model decided to call a tool
        elif event["type"] == "tool_call":
            print(f"\nTool call: {event['name']}({event['args']})")
            print("Agent (Groq): ", end="", flush=True)
        # Tool finished and returned data
        elif event["type"] == "tool_result":
            print(f"Tool result: {event['result']}")
        # Finished
        elif event["type"] == "done":
            print()


# Runs only for: python agent_groq.py
if __name__ == "__main__":
    # Stop early if Groq key is missing
    if not os.getenv("GROQ_API_KEY"):
        print("Missing GROQ_API_KEY in .env — get one from https://console.groq.com")
        raise SystemExit(1)

    # Prepare database tables + sample data
    init_db()
    # Show which Groq model is active
    print(f"Using Groq model: {GROQ_MODEL}")
    # Tell student this is local-only demo
    print("Local only. Type quit to exit.\n")

    # Terminal chat loop
    while True:
        # Read user input
        user = input("You: ").strip()
        # Allow quit / exit to stop
        if user.lower() in ("quit", "exit"):
            break
        # Run Groq agent for this message
        run_agent(user)
        # Blank line between turns
        print()
