"""
Moduł implementujący interfejs webowy dla asystenta AI.
Wykorzystuje FastAPI do obsługi zapytań HTTP oraz WebSocket do komunikacji w czasie rzeczywistym.
"""

import os
from pathlib import Path
from typing import List, Dict, AsyncGenerator
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
import asyncio
from datetime import datetime

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
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
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

# --- Chat Interface ---
@router.get("/chat", response_class=HTMLResponse)
async def chat_interface():
    """Load the chat interface."""
    try:
        with open("static/chat.html", "r") as f:
            return f.read()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error loading chat interface: {str(e)}"
        )

# --- File Upload ---
@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file for processing."""
    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No filename provided"
            )
            
        # Save file
        file_path = Path("uploads") / file.filename
        file_path.parent.mkdir(exist_ok=True)
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Process file
        await rag_manager.add_document(str(file_path))
        
        return {"filename": file.filename, "status": "success"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

# --- Document Management ---
@router.get("/documents")
async def list_documents():
    """List all processed documents."""
    try:
        documents = rag_manager.list_documents()
        return {"documents": documents}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing documents: {str(e)}"
        )
