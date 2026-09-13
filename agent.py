import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from db import init_db
from tools import (
    add_event,
    college_faq,
    create_reminder,
    generate_certificate,
    list_reminders,
    search_events,
)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Tool definitions — tell the model what tools exist
TOOLS = [
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
    {
        "type": "function",
        "function": {
            "name": "list_reminders",
            "description": "List all saved reminders",
            "parameters": {"type": "object", "properties": {}},
        },
    },
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
    """Run the Python function for the tool the model chose."""
    if name == "search_events":
        return search_events(arguments["query"])
    if name == "create_reminder":
        return create_reminder(arguments["text"])
    if name == "list_reminders":
        return list_reminders()
    if name == "add_event":
        return add_event(arguments["title"], arguments["date"], arguments["location"])
    if name == "college_faq":
        return college_faq(arguments["topic"])
    if name == "generate_certificate":
        return generate_certificate(arguments["name"])
    return f"Unknown tool: {name}"


def stream_agent(user_message):
    """
    Yields small events (for API streaming + CLI):
      {"type": "delta", "text": "..."}
      {"type": "tool_call", "name": "...", "args": {...}}
      {"type": "tool_result", "result": "..."}
      {"type": "done"}
    """
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

    while True:
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            stream=True,
        )

        full_text = ""
        collected_tools = {}

        for chunk in stream:
            delta = chunk.choices[0].delta

            if delta.content:
                full_text += delta.content
                yield {"type": "delta", "text": delta.content}

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

        if not collected_tools:
            yield {"type": "done"}
            return

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

        for t in collected_tools.values():
            name = t["name"]
            args = json.loads(t["arguments"])
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
    """CLI helper: print streamed text live."""
    print("Agent: ", end="", flush=True)
    for event in stream_agent(user_message):
        if event["type"] == "delta":
            print(event["text"], end="", flush=True)
        elif event["type"] == "tool_call":
            print(f"\nTool call: {event['name']}({event['args']})")
            print("Agent: ", end="", flush=True)
        elif event["type"] == "tool_result":
            print(f"Tool result: {event['result']}")
        elif event["type"] == "done":
            print()


if __name__ == "__main__":
    init_db()

    while True:
        user = input("You: ").strip()
        if user.lower() in ("quit", "exit"):
            break
        run_agent(user)
        print()
