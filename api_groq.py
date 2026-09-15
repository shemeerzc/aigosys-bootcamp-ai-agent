# ============================================================
# Local FastAPI for the Groq campus agent (local only)
# Run:
#   uvicorn api_groq:app --reload --host 127.0.0.1 --port 8071
# ============================================================

# Import json — format SSE payloads as JSON strings
import json

# Import FastAPI app framework
from fastapi import FastAPI
# Import CORS so browsers can call this local API
from fastapi.middleware.cors import CORSMiddleware
# Import BaseModel to validate {"message": "..."}
from pydantic import BaseModel
# Import StreamingResponse for Server-Sent Events
from starlette.responses import StreamingResponse

# Import Groq stream_agent (not the OpenAI one)
from agent_groq import stream_agent
# Import DB init for startup
from db import init_db

# Create FastAPI app with a clear title
app = FastAPI(title="Campus Agent API (Groq — local)")

# Allow all origins for local workshop demos
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    # Required chat message from the client
    message: str


# Run this function automatically when uvicorn starts
@app.on_event("startup")
def startup():
    # Create tables / seed data before handling requests
    init_db()


# Health check — includes provider info
@app.get("/api/health")
def health():
    # JSON response so students know this is the Groq local API
    return {"status": "ok", "provider": "groq", "mode": "local"}


# Main chat endpoint — streams Groq agent events with SSE
@app.post("/api/agent/chat")
def chat(body: ChatRequest):
    """SSE streaming chat — same event shape as api.py"""

    # Inner generator that produces SSE lines
    def event_stream():
        try:
            # Ask Groq agent and stream every event
            for event in stream_agent(body.message):
                # SSE format requires: data: <json>\n\n
                yield f"data: {json.dumps(event)}\n\n"
        # If anything crashes, send error then done
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
