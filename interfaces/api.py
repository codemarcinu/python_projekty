"""
Moduł implementujący API REST dla asystenta AI.
Wykorzystuje FastAPI do obsługi zapytań HTTP oraz WebSocket do komunikacji w czasie rzeczywistym.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, AsyncGenerator, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
import aiofiles
import asyncio
from datetime import datetime, timedelta

# Importujemy nasz gotowy silnik AI i menedżera konwersacji
from core.ai_engine import AIEngine, get_ai_engine
from core.conversation_handler import get_conversation_manager
from core.config_manager import get_settings

# Initialize core components
ai_engine = get_ai_engine()
conversation_manager = get_conversation_manager()
config_manager = get_settings()

# --- Security Configuration ---
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)

# Rate limiting configuration
RATE_LIMIT_WINDOW = 3600  # 1 hour
MAX_REQUESTS_PER_WINDOW = 100

# File upload configuration
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_MIME_TYPES = {
    'application/pdf': '.pdf',
    'text/plain': '.txt',
    'text/markdown': '.md'
}

# --- Models ---
class ChatRequest(BaseModel):
    message: str
    user_id: str
    model: str = "gemma3:12b"
    use_rag: bool = True

class RateLimitInfo(BaseModel):
    remaining_requests: int
    reset_time: datetime

# --- Rate Limiting ---
class RateLimiter:
    def __init__(self):
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_rate_limited(self, user_id: str) -> bool:
        now = datetime.now()
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Remove old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < timedelta(seconds=RATE_LIMIT_WINDOW)
        ]
        
        return len(self.requests[user_id]) >= MAX_REQUESTS_PER_WINDOW
    
    def add_request(self, user_id: str):
        now = datetime.now()
        if user_id not in self.requests:
            self.requests[user_id] = []
        self.requests[user_id].append(now)
    
    def get_rate_limit_info(self, user_id: str) -> RateLimitInfo:
        now = datetime.now()
        if user_id not in self.requests:
            return RateLimitInfo(remaining_requests=MAX_REQUESTS_PER_WINDOW, reset_time=now)
        
        # Remove old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < timedelta(seconds=RATE_LIMIT_WINDOW)
        ]
        
        remaining = MAX_REQUESTS_PER_WINDOW - len(self.requests[user_id])
        reset_time = now + timedelta(seconds=RATE_LIMIT_WINDOW)
        
        return RateLimitInfo(remaining_requests=remaining, reset_time=reset_time)

# Initialize rate limiter
rate_limiter = RateLimiter()

# --- API Setup ---
router = APIRouter()

# --- Security Dependencies ---
async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != config_manager.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return api_key

async def check_rate_limit(user_id: str):
    if rate_limiter.is_rate_limited(user_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
    rate_limiter.add_request(user_id)

# --- File Upload Validation ---
async def validate_file(file: UploadFile) -> Path:
    if not file or not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided"
        )
        
    # Check file size
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    
    # Create temporary file for size check
    temp_path = Path(f"temp_{file.filename}")
    try:
        async with aiofiles.open(temp_path, 'wb') as temp_file:
            while chunk := await file.read(chunk_size):
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too large. Maximum size is {MAX_FILE_SIZE/1024/1024}MB"
                    )
                await temp_file.write(chunk)
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_MIME_TYPES.values():
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed types: {', '.join(ALLOWED_MIME_TYPES.values())}"
            )
        
        # Sanitize filename
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._- ")
        safe_filename = safe_filename[:255]  # Limit filename length
        
        # Move to final location
        final_path = Path("uploads") / safe_filename
        final_path.parent.mkdir(exist_ok=True)
        shutil.move(str(temp_path), str(final_path))
        
        return final_path
        
    finally:
        # Clean up temporary file if it exists
        if temp_path.exists():
            temp_path.unlink()

# --- API Endpoints ---
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Upload a file for processing."""
    try:
        file_path = await validate_file(file)
        return {"filename": file_path.name, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/chat")
async def chat(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    """Process a chat message."""
    await check_rate_limit(request.user_id)
    
    try:
        response = await ai_engine.process_message(
            message=request.message,
            model=request.model,
            use_rag=request.use_rag
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rate-limit")
async def get_rate_limit(
    user_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get rate limit information for a user."""
    return rate_limiter.get_rate_limit_info(user_id)

@router.get("/health")
async def health_check():
    """Check the health status of the API."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "llm_status": ai_engine.llm_manager.get_health_status()
    }

# --- WebSocket Connection ---
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            await check_rate_limit(user_id)
            
            try:
                response = await ai_engine.process_message(
                    message=message,
                    model="gemma3:12b",
                    use_rag=True
                )
                await websocket.send_text(response)
            except Exception as e:
                await websocket.send_text(f"Error: {str(e)}")
    except WebSocketDisconnect:
        pass
