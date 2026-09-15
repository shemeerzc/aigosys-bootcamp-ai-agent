# Import json — used to parse tool arguments from the model
import json
# Import os — used to read OPENAI_API_KEY from environment
import os

# Import load_dotenv — loads secrets from .env file
from dotenv import load_dotenv
# Import OpenAI client — talks to OpenAI Chat Completions API
from openai import OpenAI

# Import init_db — creates tables / sample data on startup
from db import init_db
# Import all tool functions the agent is allowed to call
from tools import (
    add_event,
    college_faq,
    create_reminder,
    generate_certificate,
    list_reminders,
    search_events,
)

# Load .env values into environment variables
load_dotenv()
# Create OpenAI client using the API key from .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# TOOLS = JSON schemas that describe tools to the LLM (not Python code)
TOOLS = [
    # ---- tool 1: search_events ----
    {
        # OpenAI tool type is always "function" for function calling
        "type": "function",
        # Function details the model can choose
        "function": {
            # Exact name must match call_tool() below
            "name": "search_events",
            # Plain-English description helps the model decide when to use it
            "description": (
                "Search college events. Use empty query or 'all' for every event. "
                "For one event pass main keywords only (e.g. cyber, workshop, AI)."
            ),
            # JSON Schema for arguments
            "parameters": {
                "type": "object",
                # Argument fields
                "properties": {
                    # One argument named query
                    "query": {
                        "type": "string",
                        "description": "Keyword to search in event title or location",
                    }
                },
                # query is required
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
    """Run the matching Python tool function chosen by the model."""
    # If model asked for search_events, run that function
    if name == "search_events":
        return search_events(arguments["query"])
    # If model asked for create_reminder, run that function
    if name == "create_reminder":
        return create_reminder(arguments["text"])
    # If model asked for list_reminders, run that function
    if name == "list_reminders":
        return list_reminders()
    # If model asked for add_event, pass title/date/location
    if name == "add_event":
        return add_event(arguments["title"], arguments["date"], arguments["location"])
    # If model asked for college_faq, pass topic
    if name == "college_faq":
        return college_faq(arguments["topic"])
    # If model asked for generate_certificate, pass student name
    if name == "generate_certificate":
        return generate_certificate(arguments["name"])
    # Unknown tool name — return error text
    return f"Unknown tool: {name}"


def stream_agent(user_message):
    """
    Main agent loop with streaming.
    Yields small events for CLI + API:
      {"type": "delta", "text": "..."}
      {"type": "tool_call", "name": "...", "args": {...}}
      {"type": "tool_result", "result": "..."}
      {"type": "done"}
    """
    # Start chat history with system rules + user question
    messages = [
        {
            # system = instructions for the model
            "role": "system",
            "content": (
                "You are a helpful campus assistant. "
                "Use tools for events, reminders, FAQ, and certificates when needed."
            ),
        },
        # user = the real question from the student
        {"role": "user", "content": user_message},
    ]

    # Loop until the model gives a final text answer (no more tools)
    while True:
        # Call OpenAI with streaming enabled
        stream = client.chat.completions.create(
            # Small, cheap model good for teaching demos
            model="gpt-4o-mini",
            # Full conversation so far
            messages=messages,
            # Tell the model which tools exist
            tools=TOOLS,
            # stream=True → answer comes in small pieces
            stream=True,
        )

        # Collect full text from all stream chunks
        full_text = ""
        # Collect tool-call pieces (they also arrive in chunks)
        collected_tools = {}

        # Read each streamed chunk from the API
        for chunk in stream:
            # delta = the new piece in this chunk
            delta = chunk.choices[0].delta

            # If this chunk has normal text, stream it out
            if delta.content:
                # Add to full reply text
                full_text += delta.content
                # Yield one delta event for CLI/API
                yield {"type": "delta", "text": delta.content}

            # If this chunk has tool-call fragments, collect them
            if delta.tool_calls:
                # A chunk may contain one or more tool call parts
                for tc in delta.tool_calls:
                    # index groups pieces of the same tool call
                    i = tc.index
                    # First time we see this index → create empty collector
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
                    # Arguments arrive as partial JSON strings — append them
                    if tc.function and tc.function.arguments:
                        collected_tools[i]["arguments"] += tc.function.arguments

        # No tools requested → this was the final answer
        if not collected_tools:
            # Tell consumer streaming is finished
            yield {"type": "done"}
            # Exit the agent loop
            return

        # Save the assistant's tool request into chat history
        messages.append(
            {
                "role": "assistant",
                # May be empty if model only requested tools
                "content": full_text or None,
                # List of tool calls the model requested
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
            # Parse JSON arguments string into a Python dict
            args = json.loads(t["arguments"])
            # Notify CLI/API which tool is running
            yield {"type": "tool_call", "name": name, "args": args}

            # Execute the real Python tool
            result = call_tool(name, args)
            # Send tool output to CLI/API
            yield {"type": "tool_result", "result": str(result)}

            # Add tool result back into chat history for the next LLM call
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": t["id"],
                    "content": str(result),
                }
            )


def run_agent(user_message):
    """CLI helper: print streamed events live in the terminal."""
    # Print prefix before streamed text
    print("Agent: ", end="", flush=True)
    # Consume every event from stream_agent
    for event in stream_agent(user_message):
        # Normal answer text piece
        if event["type"] == "delta":
            print(event["text"], end="", flush=True)
        # Model decided to call a tool
        elif event["type"] == "tool_call":
            print(f"\nTool call: {event['name']}({event['args']})")
            print("Agent: ", end="", flush=True)
        # Tool finished and returned data
        elif event["type"] == "tool_result":
            print(f"Tool result: {event['result']}")
        # Finished
        elif event["type"] == "done":
            print()


# Runs only when you type: python agent.py
if __name__ == "__main__":
    # Make sure DB tables + sample data exist
    init_db()

    # Simple chat loop in the terminal
    while True:
        # Read user input
        user = input("You: ").strip()
        # Allow quit / exit to stop
        if user.lower() in ("quit", "exit"):
            break
        # Run the streaming agent for this message
        run_agent(user)
        # Blank line between turns
        print()
