"""
Główny plik aplikacji FastAPI z obsługą WebSocket i nowego frontendu.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import logging
import json
from datetime import datetime
import asyncio

from core.ai_engine import AIEngine, get_ai_engine
from core.conversation_handler import get_conversation_manager
from core.config_manager import get_settings
from core.rag_manager import RAGManager
from core.auth import get_current_user, User

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Inicjalizacja komponentów
app = FastAPI(title="AI Assistant API")
ai_engine = get_ai_engine()
conversation_manager = get_conversation_manager()
config_manager = get_settings()
rag_manager = RAGManager(
    model_name=config_manager.rag.embedding_model,
    trust_remote_code=config_manager.rag.trust_remote_code
)

@app.on_event("startup")
async def startup_event():
    """Inicjalizacja komponentów przy starcie aplikacji."""
    try:
        await rag_manager.initialize()
        logger.info("RAG manager initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing RAG manager: {e}")
        raise

# Konfiguracja CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # W produkcji należy to ograniczyć
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modele Pydantic
class ChatMessage(BaseModel):
    content: str
    role: str
    timestamp: Optional[datetime] = None

class ChatResponse(BaseModel):
    message: str
    timestamp: datetime

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connection established for client {client_id}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket connection closed for client {client_id}")

    async def send_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)
            logger.debug(f"Message sent to client {client_id}")

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

# Endpointy API
@app.get("/api/health")
async def health_check():
    """Sprawdzenie stanu API."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Endpoint WebSocket do obsługi komunikacji w czasie rzeczywistym."""
    try:
        await manager.connect(websocket, client_id)
        
        # Inicjalizacja konwersacji
        conversation_id = conversation_manager.create_conversation(client_id)
        logger.info(f"Created conversation {conversation_id} for client {client_id}")
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Przetwarzanie wiadomości
                response = await ai_engine.process_message(
                    message=message["content"],
                    conversation_id=conversation_id
                )
                
                # Wysyłanie odpowiedzi
                await manager.send_message(
                    json.dumps({
                        "type": "message",
                        "content": response,
                        "timestamp": datetime.now().isoformat()
                    }),
                    client_id
                )
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for client {client_id}")
                break
            except Exception as e:
                error_msg = f"Error processing message: {str(e)}"
                logger.error(error_msg, exc_info=True)
                await manager.send_message(
                    json.dumps({
                        "type": "error",
                        "message": error_msg
                    }),
                    client_id
                )
                
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {str(e)}", exc_info=True)
    finally:
        manager.disconnect(client_id)
        try:
            conversation_manager.end_conversation(conversation_id)
            logger.info(f"Ended conversation {conversation_id} for client {client_id}")
        except:
            pass

@app.get("/api/models")
async def list_models(current_user: User = Depends(get_current_user)):
    """Lista dostępnych modeli AI."""
    try:
        models = await ai_engine.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing models: {str(e)}"
        )

@app.post("/api/chat")
async def chat_endpoint(
    message: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    """Endpoint do wysyłania wiadomości czatu."""
    try:
        response = await ai_engine.process_message(
            message=message.content,
            conversation_id=current_user.id
        )
        return ChatResponse(
            message=response,
            timestamp=datetime.now()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing message: {str(e)}"
        )

# Montowanie statycznych plików z frontendu
if os.path.exists("frontend/.svelte-kit/output/client"):
    app.mount("/", StaticFiles(directory="frontend/.svelte-kit/output/client", html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        """Strona główna aplikacji."""
        return {"message": "AI Assistant API", "status": "running", "version": "1.0.0"}

# Middleware do obsługi błędów
@app.middleware("http")
async def error_handler(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config_manager.host,
        port=config_manager.port,
        reload=config_manager.debug
    )
