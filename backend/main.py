import os
import logging
from typing import Dict, List, Any
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

from backend.security.input_validation import sanitize_and_validate_input, ValidationError
from backend.security.rate_limiter import global_rate_limiter
from backend.orchestrator import run_chat_turn
from backend.config import DB_PATH
from backend.data.init_db import init_db

# Setup logging
logger: logging.Logger = logging.getLogger("stadium-main")
logging.basicConfig(level=logging.INFO)

app: FastAPI = FastAPI(
    title="FIFA 2026 Stadium Navigation & Info Assistant",
    description="Accessible, multilingual chat & voice assistant for stadium navigation.",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event() -> None:
    """FastAPI startup event handler.

    Automatically initializes and seeds the SQLite venue database if it does not
    exist at DB_PATH. This is critical on serverless platforms (e.g. Vercel)
    where the database is created in /tmp on startup.
    """
    if not os.path.exists(DB_PATH):
        logger.info("Database not found at %s. Initializing and seeding...", DB_PATH)
        init_db()
    else:
        logger.info("Database already exists at %s.", DB_PATH)

# In-memory session history store: { session_id: list of messages }
session_histories: Dict[str, List[Dict[str, Any]]] = {}

class ChatRequest(BaseModel):
    """Schema for chat requests."""
    session_id: str = Field(..., description="Unique ID for client session")
    message: str = Field(..., description="User message to process")

def check_rate_limit(request: Request) -> None:
    """FastAPI dependency to enforce IP-based rate limits.

    Args:
        request: The incoming FastAPI HTTP request.

    Raises:
        HTTPException: If the client host is over their rate limit.
    """
    client_ip: str = request.client.host if request.client else "unknown_ip"
    if not global_rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait before typing again."
        )

@app.post("/api/chat")
async def chat_endpoint(
    chat_req: ChatRequest,
    request: Request,
    _: None = Depends(check_rate_limit)
) -> Any:
    """Handles fan chat queries.

    Sanitizes the user message, updates conversation history, and routes the query
    through the AI orchestrator or local mock fallback.

    Args:
        chat_req: The validated ChatRequest body containing message and session ID.
        request: The FastAPI request object.
        _: Rate limit dependency.

    Returns:
        A JSON response containing the assistant reply and the session ID.
    """
    try:
        # Sanitize and validate input text
        sanitized_msg: str = sanitize_and_validate_input(chat_req.message)
    except ValidationError as ve:
        return JSONResponse(
            status_code=400,
            content={"error": str(ve)}
        )
    
    # Initialize history if session is new
    session_id: str = chat_req.session_id
    if session_id not in session_histories:
        session_histories[session_id] = []
        
    history: List[Dict[str, Any]] = session_histories[session_id]
    
    # Run orchestrator turn
    reply: str = run_chat_turn(session_id, sanitized_msg, history)
    
    return {
        "reply": reply,
        "session_id": session_id
    }

# Serve frontend static files
FRONTEND_DIR: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "frontend"
)

@app.get("/")
async def get_index() -> Any:
    """Serves the main frontend index.html page.

    Returns:
        FileResponse of the index.html page, or JSONResponse error if missing.
    """
    index_path: str = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(status_code=404, content={"error": "Frontend assets not found."})

# If frontend files exist, mount them
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")
