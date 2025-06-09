"""
FastAPI web interface for the AI Assistant.
Provides endpoints for chat interaction and document management.
"""
from pathlib import Path
from typing import List, Optional, Dict
from uuid import uuid4
from datetime import datetime
import logging
import json
import psutil

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from core.ai_engine import get_ai_engine
from core.conversation_handler import get_conversation_manager, Conversation
from core.llm_manager import get_llm_manager
from core.rag_manager import RAGManager
from core.config_manager import get_settings

# Configure logging
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Assistant")

# Konfiguracja CORS
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://localhost:3000",  # Dla React development server
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Mount static files
static_path = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Initialize managers
llm_manager = get_llm_manager()
rag_manager = RAGManager(get_settings().rag)

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}

class ChatMessage(BaseModel):
    """Model for chat messages."""
    role: str
    content: str
    model: Optional[str] = "gemma3:12b"
    use_rag: Optional[bool] = True

class ChatResponse(BaseModel):
    """Model for chat responses."""
    message: str
    conversation_id: str
    model: str
    timestamp: datetime

async def get_websocket_token(websocket: WebSocket) -> str:
    """Validate WebSocket connection and return token."""
    try:
        # Accept the connection first
        await websocket.accept()
        
        # Get token from query parameters
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="Missing token")
            raise HTTPException(status_code=403, detail="Missing token")
            
        # Here you would validate the token
        # For now, we'll just check if it's not empty
        if not token.strip():
            await websocket.close(code=4002, reason="Invalid token")
            raise HTTPException(status_code=403, detail="Invalid token")
            
        return token
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=4003, reason="Authentication failed")
        raise HTTPException(status_code=403, detail="Authentication failed")

@app.get("/", response_class=HTMLResponse)
async def get_chat_interface():
    """Zwraca interfejs czatu."""
    try:
        with open(static_path / "index.html", "r") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error loading chat interface: {e}")
        raise HTTPException(status_code=500, detail="Błąd ładowania interfejsu czatu")

@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str, request: Request):
    """WebSocket endpoint for real-time chat."""
    try:
        # Get origin from request headers
        origin = request.headers.get('origin')
        
        # Validate origin
        if origin and origin not in origins:
            logger.warning(f"Rejected WebSocket connection from invalid origin: {origin}")
            await websocket.close(code=4003, reason="Invalid origin")
            return
        
        # Accept the connection
        await websocket.accept()
        
        logger.info(f"WebSocket connection established for conversation {conversation_id}")
        
        # Initialize AI engine
        ai_engine = get_ai_engine()
        
        # Add to active connections
        active_connections[conversation_id] = websocket
        
        try:
            while True:
                try:
                    # Receive message
                    data = await websocket.receive_text()
                    
                    try:
                        message = json.loads(data)
                    except json.JSONDecodeError:
                        logger.error("Received invalid JSON from client")
                        await websocket.send_json({
                            "type": "error",
                            "content": "Invalid message format"
                        })
                        continue
                    
                    # Process message
                    try:
                        response = await ai_engine.process_message(
                            message.get("content", ""),
                            conversation_id
                        )
                        
                        # Send response
                        await websocket.send_json({
                            "type": "chat",
                            "content": response,
                            "role": "assistant"
                        })
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "content": str(e)
                        })
                        
                except WebSocketDisconnect:
                    logger.info(f"WebSocket connection closed for conversation {conversation_id}")
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            
    except Exception as e:
        logger.error(f"Error in WebSocket connection: {e}")
        
    finally:
        # Clean up
        if conversation_id in active_connections:
            del active_connections[conversation_id]

async def send_stats_update(websocket: WebSocket):
    """Send current stats to the client."""
    try:
        stats = await get_current_stats()
        await websocket.send_json({
            "type": "stats",
            "data": stats
        })
    except Exception as e:
        logger.error(f"Error sending stats update: {e}")

async def get_current_stats() -> Dict:
    """Get current system stats."""
    try:
        # Get model status
        model_status = await llm_manager.get_model_status()
        
        # Get document count
        doc_count = rag_manager.get_document_count()
        
        # Get memory usage
        memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        return {
            "active_model": model_status["model"],
            "status": model_status["status"],
            "doc_count": doc_count,
            "memory_usage": f"{memory:.1f} MB"
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "active_model": "unknown",
            "status": "error",
            "doc_count": 0,
            "memory_usage": "0 MB"
        }

@app.get("/api/stats")
async def get_stats():
    """Get current system stats."""
    return await get_current_stats()

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a document for RAG processing."""
    try:
        # Validate file size (50MB limit)
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(
                status_code=400,
                detail="File too large. Maximum size is 50MB."
            )
            
        # Save file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
            
        file_path = Path("uploads") / file.filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, "wb") as f:
            f.write(content)
            
        # Process with RAG
        success = await rag_manager.add_document(str(file_path))
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to process document"
            )
            
        return {"message": "File uploaded and processed successfully"}
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error processing file"
        )

@app.delete("/api/documents/{file_id}")
async def delete_document(file_id: str):
    """Delete a document from the RAG system."""
    try:
        if rag_manager.delete_document(file_id):
            return {"success": True, "message": "Document deleted successfully"}
        raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting document: {str(e)}"
        )

@app.get("/api/documents")
async def list_documents():
    """List all documents in the RAG system."""
    try:
        documents = rag_manager.list_documents()
        return {
            "success": True,
            "documents": documents
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listing documents: {str(e)}"
        )
