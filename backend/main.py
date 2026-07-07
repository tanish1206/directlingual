import os
from typing import Dict, List, Any
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

from backend.security.input_validation import sanitize_and_validate_input, ValidationError
from backend.security.rate_limiter import global_rate_limiter
from backend.orchestrator import run_chat_turn

app = FastAPI(
    title="FIFA 2026 Stadium Navigation & Info Assistant",
    description="Accessible, multilingual chat & voice assistant for stadium navigation.",
    version="1.0.0"
)

# In-memory session history store: { session_id: list of messages }
session_histories: Dict[str, List[Dict[str, Any]]] = {}

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique ID for client session")
    message: str = Field(..., description="User message to process")

# Rate Limiter dependency
def check_rate_limit(request: Request):
    # Retrieve client IP as identifier
    client_ip = request.client.host if request.client else "unknown_ip"
    if not global_rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many requests. Please wait before typing again.")

@app.post("/api/chat")
async def chat_endpoint(chat_req: ChatRequest, request: Request, _=Depends(check_rate_limit)):
    try:
        # Sanitize and validate input text
        sanitized_msg = sanitize_and_validate_input(chat_req.message)
    except ValidationError as ve:
        return JSONResponse(
            status_code=400,
            content={"error": str(ve)}
        )
    
    # Initialize history if session is new
    session_id = chat_req.session_id
    if session_id not in session_histories:
        session_histories[session_id] = []
        
    history = session_histories[session_id]
    
    # Run orchestrator turn
    reply = run_chat_turn(session_id, sanitized_msg, history)
    
    return {
        "reply": reply,
        "session_id": session_id
    }

# Serve frontend static files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

@app.get("/")
async def get_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(status_code=404, content={"error": "Frontend assets not found."})

# If frontend files exist, mount them
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")
