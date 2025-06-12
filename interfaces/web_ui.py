"""
Moduł implementujący interfejs webowy dla asystenta AI.
Wykorzystuje FastAPI do obsługi zapytań HTTP oraz WebSocket do komunikacji w czasie rzeczywistym.
"""

import os
from pathlib import Path
from typing import List, Dict, AsyncGenerator, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, File, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
import asyncio
from datetime import datetime, timedelta
import logging
import json
from collections import defaultdict
import time

# Importujemy nasz gotowy silnik AI i menedżera konwersacji
from core.ai_engine import AIEngine, get_ai_engine
from core.conversation_handler import get_conversation_manager
from core.config_manager import get_settings
from core.rag_manager import RAGManager

# Initialize core components
ai_engine = get_ai_engine()
conversation_manager = get_conversation_manager()
config_manager = get_settings()
rag_manager = RAGManager(config_manager.rag)

# --- Security Configuration ---
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME)

# --- Rate Limiting ---
class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
    
    def is_rate_limited(self, client_id: str) -> bool:
        now = time.time()
        minute_ago = now - 60
        
        # Usuń stare requesty
        self.requests[client_id] = [req_time for req_time in self.requests[client_id] if req_time > minute_ago]
        
        # Sprawdź limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return True
        
        # Dodaj nowy request
        self.requests[client_id].append(now)
        return False

rate_limiter = RateLimiter(requests_per_minute=60)

# --- Rate Limiting Middleware ---
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_id = request.client.host if request.client else "unknown"
        
        if rate_limiter.is_rate_limited(client_id):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."}
            )
        
        response = await call_next(request)
        return response

# --- Models ---
class ChatMessage(BaseModel):
    content: str
    role: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatResponse(BaseModel):
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)

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

# --- WebSocket Connection ---
@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    Endpoint WebSocket do obsługi komunikacji w czasie rzeczywistym.
    """
    try:
        await websocket.accept()
        logging.info(f"WebSocket connection accepted for user {user_id}")
        
        # Inicjalizacja konwersacji
        conversation_id = conversation_manager.create_conversation(user_id)
        logging.info(f"Created conversation {conversation_id} for user {user_id}")
        
        # Inicjalizacja RAG jeśli potrzebne
        if not rag_manager.model or not rag_manager.index:
            await rag_manager.initialize()
        
        while True:
            try:
                # Odbierz wiadomość (JSON lub tekst)
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    message = msg.get('content', '')
                except Exception:
                    message = data
                
                logging.debug(f"Received message from user {user_id}: {message[:100]}...")
                
                # Sprawdź rate limiting dla WebSocket
                if rate_limiter.is_rate_limited(user_id):
                    await websocket.send_json({
                        "type": "error",
                        "message": "Too many messages. Please wait a moment."
                    })
                    continue
                
                # Przetwórz wiadomość
                response = await ai_engine.process_message(
                    message=message,
                    conversation_id=user_id
                )
                
                await websocket.send_json({
                    "type": "message",
                    "content": response
                })
                
                logging.debug(f"Sent response to user {user_id}: {response[:100]}...")
                
            except WebSocketDisconnect:
                logging.info(f"WebSocket disconnected for user {user_id}")
                break
            except Exception as e:
                error_msg = f"Error processing message: {str(e)}"
                logging.error(error_msg, exc_info=True)
                await websocket.send_json({
                    "type": "error",
                    "message": error_msg
                })
                
    except Exception as e:
        logging.error(f"WebSocket error for user {user_id}: {str(e)}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    finally:
        try:
            conversation_manager.end_conversation(conversation_id.id)
            logging.info(f"Ended conversation {conversation_id.id} for user {user_id}")
        except:
            pass

# --- Chat Interface ---
@router.get("/chat", response_class=HTMLResponse)
async def chat_interface():
    """Load the chat interface."""
    try:
        with open("static/index.html", "r") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading chat interface: {str(e)}"
        )

# --- File Upload ---
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Upload a file for processing."""
    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No filename provided"
            )
        
        # Sprawdź rozmiar pliku
        file_size = 0
        content = bytearray()
        
        while chunk := await file.read(8192):
            file_size += len(chunk)
            if file_size > config_manager.max_file_size:
                raise HTTPException(
                    status_code=413,
                    detail="File too large"
                )
            content.extend(chunk)
        
        # Sprawdź typ pliku
        allowed_types = {'.txt', '.pdf', '.doc', '.docx', '.md'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=415,
                detail="Unsupported file type"
            )
        
        # Zapisz plik
        file_path = Path(config_manager.upload_dir) / file.filename
        file_path.parent.mkdir(exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Przetwórz plik
        await rag_manager.add_document(str(file_path))
        
        return {
            "filename": file.filename,
            "status": "success",
            "size": file_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

# --- Document Management ---
@router.get("/documents")
async def list_documents(api_key: str = Depends(verify_api_key)):
    """List all processed documents."""
    try:
        documents = rag_manager.list_documents()
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing documents: {str(e)}"
        )
