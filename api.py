# Import json — used to format SSE event payloads
import json

# Import FastAPI — web framework for the API
from fastapi import FastAPI
# Import CORS middleware — allows browser frontends to call this API
from fastapi.middleware.cors import CORSMiddleware
# Import BaseModel — validates JSON request body
from pydantic import BaseModel
# Import StreamingResponse — sends SSE chunks to the client
from starlette.responses import StreamingResponse

# Import stream_agent — OpenAI campus agent generator
from agent import stream_agent
# Import init_db — prepare SQLite on startup
from db import init_db

# Create the FastAPI application object
app = FastAPI(title="Campus Agent API")

# Enable CORS so any frontend origin can call the API (workshop-friendly)
app.add_middleware(
    CORSMiddleware,
    # Allow all websites (OK for teaching demos)
    allow_origins=["*"],
    # Allow all HTTP methods
    allow_methods=["*"],
    # Allow all headers
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    # The user chat message sent as JSON: {"message": "..."}
    message: str


# Run this function automatically when the server starts
@app.on_event("startup")
def startup():
    # Create tables / seed data before handling requests
    init_db()


# Health check endpoint — used to verify the API is alive
@app.get("/api/health")
def health():
    # Simple JSON response
    return {"status": "ok"}


# Main chat endpoint — streams agent events with SSE
@app.post("/api/agent/chat")
def chat(body: ChatRequest):
    """
    Public chat endpoint (SSE streaming).
    Each line: data: {"type": "delta"|"tool_call"|"tool_result"|"done", ...}
    """

    # Inner generator that produces SSE lines
    def event_stream():
        try:
            # Ask the agent and stream every event
            for event in stream_agent(body.message):
                # SSE format requires: data: <json>\n\n
                yield f"data: {json.dumps(event)}\n\n"
        # If anything crashes, send an error event then done
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    # Return a streaming HTTP response
    return StreamingResponse(
        # Generator of SSE chunks
        event_stream(),
        # Content type for Server-Sent Events
        media_type="text/event-stream",
        # Extra headers to keep the stream open
        headers={
            # Do not cache streamed responses
            "Cache-Control": "no-cache",
            # Keep TCP connection alive during stream
            "Connection": "keep-alive",
        },
    )
