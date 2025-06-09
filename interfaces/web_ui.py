"""
FastAPI web interface for the AI Assistant.
Provides endpoints for chat interaction and document management.
"""
from pathlib import Path
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from core.ai_engine import get_ai_engine
from core.conversation_handler import get_conversation_manager, Conversation

# Configure logging
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Assistant")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")


class ChatMessage(BaseModel):
    """Model for chat messages."""
    role: str
    content: str


class ChatResponse(BaseModel):
    """Model for chat responses."""
    message: str
    conversation_id: str


@app.get("/", response_class=HTMLResponse)
async def get_chat_interface(request: Request):
    """Serve the chat interface."""
    return templates.TemplateResponse(
        "chat.html",
        {"request": request}
    )


@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """Handle WebSocket connections for real-time chat."""
    await websocket.accept()
    logger.info(f"WebSocket connection established for conversation {conversation_id}")
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            message = data.get("message", "")
            use_agent = data.get("use_agent", False)
            
            if not message.strip():
                await websocket.send_json({
                    "error": "Wiadomość nie może być pusta"
                })
                continue
            
            try:
                # Process message through AI engine
                ai_engine = get_ai_engine()
                response = await ai_engine.process_message(
                    message=message,
                    conversation_id=conversation_id,
                    use_agent=use_agent
                )
                
                # Send response
                await websocket.send_json({
                    "response": response,
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                await websocket.send_json({
                    "error": f"Błąd przetwarzania: {str(e)}"
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed for conversation {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


@app.post("/upload", response_model=dict)
async def upload_document(file: UploadFile = File(...)):
    """Upload a document to the RAG system."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Validate file type
    allowed_types = {".pdf", ".txt", ".md"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Save file
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    
    with file_path.open("wb") as f:
        content = await file.read()
        f.write(content)
    
    # Process file with RAG system
    ai_engine = get_ai_engine()
    # TODO: Implement document processing
    
    return {"message": "Document uploaded successfully", "filename": file.filename}


@app.get("/conversations", response_model=List[dict])
async def list_conversations():
    """List all conversations."""
    conversation_manager = get_conversation_manager()
    conversations = conversation_manager.list_conversations()
    return [
        {
            "id": conv_id,
            "title": title,
            "updated_at": updated_at.isoformat()
        }
        for conv_id, title, updated_at in conversations
    ]


@app.post("/conversations", response_model=dict)
async def create_conversation():
    """Create a new conversation."""
    conversation_id = str(uuid4())
    conversation_manager = get_conversation_manager()
    conversation = conversation_manager.create_conversation(conversation_id)
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat()
    }


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    conversation_manager = get_conversation_manager()
    if conversation_manager.delete_conversation(conversation_id):
        return {"message": "Conversation deleted successfully"}
    raise HTTPException(status_code=404, detail="Conversation not found")
