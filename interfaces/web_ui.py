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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from core.ai_engine import get_ai_engine
from core.conversation_handler import get_conversation_manager, Conversation
from core.llm_manager import get_llm_manager
from core.rag_manager import RAGManager
from core.config_manager import get_settings

# Configure logging
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Assistant")

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
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    active_connections[conversation_id] = websocket
    logger.info(f"WebSocket connection established for conversation {conversation_id}")
    
    try:
        while True:
            try:
                # Odbierz wiadomość jako tekst
                raw_data = await websocket.receive_text()
                
                # Sparsuj JSON
                try:
                    data = json.loads(raw_data)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    await websocket.send_json({
                        "error": "Nieprawidłowy format JSON",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                message = data.get("message", "").strip()
                use_agent = data.get("use_agent", True)  # Domyślnie włączony agent
                
                if not message:
                    await websocket.send_json({
                        "error": "Wiadomość nie może być pusta",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue
                
                # Przetwórz wiadomość przez AI
                ai_engine = get_ai_engine()
                
                response = await ai_engine.process_message(
                    message=message,
                    conversation_id=conversation_id,
                    use_agent=use_agent
                )
                
                # Wyślij odpowiedź
                await websocket.send_json({
                    "response": response,
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat()
                })
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for conversation {conversation_id}")
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                try:
                    await websocket.send_json({
                        "error": f"Błąd przetwarzania: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    })
                except:
                    break
                    
    except Exception as e:
        logger.error(f"WebSocket error for conversation {conversation_id}: {e}")
    finally:
        try:
            if conversation_id in active_connections:
                del active_connections[conversation_id]
            await websocket.close()
        except:
            pass

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

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document to the RAG system."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Validate file type
    allowed_types = {".pdf", ".txt", ".md", ".doc", ".docx"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Validate file size (50MB limit)
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 50MB."
        )
    
    # Save file
    upload_dir = Path("uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    
    with file_path.open("wb") as f:
        f.write(content)
    
    # Process file with RAG system
    try:
        file_id = rag_manager.add_document(file_path)
        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename
        }
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
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
