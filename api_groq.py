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


# On server start, prepare SQLite
@app.on_event("startup")
def startup():
    init_db()


# Health check — includes provider info
@app.get("/api/health")
def health():
    return {"status": "ok", "provider": "groq", "mode": "local"}


# Streaming chat endpoint (same shape as api.py)
@app.post("/api/agent/chat")
def chat(body: ChatRequest):
    """SSE streaming chat — same event shape as api.py"""

    # Generator that yields SSE lines
    def event_stream():
        try:
            # Stream every Groq agent event
            for event in stream_agent(body.message):
                # SSE line format
                yield f"data: {json.dumps(event)}\n\n"
        # On error, still close the stream cleanly
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    # Return streaming HTTP response
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )
