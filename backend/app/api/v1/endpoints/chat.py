import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import StreamingResponse
import asyncio
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.websocket import manager
from app.services.conversation.service import ConversationService
from app.services.ai.service import AIService
from app.schemas.chat import ChatMessage, ChatResponse, WebSocketMessage
from app.core.auth import get_current_user, User
from app.core.deps import get_conversation_service, get_ai_service
from app.api.deps import get_ollama_service
from app.services.ollama.service import OllamaService
from app.services.ollama.exceptions import (
    OllamaServiceError, OllamaConnectionError, ModelNotFoundError,
    GenerationError, ResourceLimitError
)
from app.core.config import settings
from app.core.security import verify_token
from app.core.rate_limit import limiter
from app.services.agents.orchestrator import AgentOrchestrator
from app.api.v1.schemas.chat import (
    ChatRequest, ChatResponse, StreamResponse, ErrorResponse,
    Conversation, ConversationCreate, ConversationUpdate, Message
)

router = APIRouter()
logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    model_name: Optional[str] = settings.DEFAULT_CHAT_MODEL
    stream: bool = False
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    model_name: str
    tokens_generated: Optional[int] = None
    duration: Optional[float] = None

class ModelInfo(BaseModel):
    """Model information model."""
    name: str
    type: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    ollama_service: OllamaService = Depends(get_ollama_service)
):
    """WebSocket endpoint for streaming chat."""
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            request = json.loads(data)
            
            try:
                # Generate response
                async for chunk in ollama_service.generate(
                    prompt=request["message"],
                    model_name=request.get("model_name", settings.DEFAULT_CHAT_MODEL),
                    stream=True,
                    temperature=request.get("temperature"),
                    max_tokens=request.get("max_tokens")
                ):
                    await websocket.send_text(json.dumps({
                        "type": "chunk",
                        "content": chunk
                    }))
                
                # Send completion message
                await websocket.send_text(json.dumps({
                    "type": "complete"
                }))
                
            except OllamaServiceError as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": str(e)
                }))
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Internal server error"
            }))
        except:
            pass

@router.post("/chat", response_model=ChatResponse, responses={
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    429: {"model": ErrorResponse}
})
@limiter.limit("10/minute")
async def chat_endpoint(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    conversation_service: ConversationService = Depends(),
    ollama_service: OllamaService = Depends(),
    agent_orchestrator: AgentOrchestrator = Depends()
):
    """
    Process a chat message and return the response.
    
    - **message**: The message content
    - **conversation_id**: Optional ID of existing conversation
    - **stream**: Whether to stream the response
    - **model**: Optional model to use
    - **temperature**: Optional temperature for generation
    - **max_tokens**: Optional maximum tokens to generate
    """
    try:
        # Get or create conversation
        if request.conversation_id:
            conversation = await conversation_service.get_conversation(request.conversation_id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
        else:
            conversation = await conversation_service.create_conversation(
                title=f"Chat with {current_user.username}",
                initial_message=request.message
            )

        # Process message through agent orchestrator
        response = await agent_orchestrator.process(
            message=request.message,
            conversation_id=conversation.id,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        # Add response to conversation
        await conversation_service.add_message(
            conversation_id=conversation.id,
            content=response.content,
            role="assistant",
            metadata=response.metadata
        )

        return ChatResponse(
            conversation_id=conversation.id,
            message=response,
            model=response.metadata.get("model", settings.DEFAULT_CHAT_MODEL),
            usage=response.metadata.get("usage", {})
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_service: ConversationService = Depends(),
    ollama_service: OllamaService = Depends(),
    agent_orchestrator: AgentOrchestrator = Depends()
):
    """
    WebSocket endpoint for real-time chat.
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            request = ChatRequest.parse_raw(data)
            
            # Process message
            response = await agent_orchestrator.process(
                message=request.message,
                conversation_id=request.conversation_id,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True
            )
            
            # Stream response
            async for chunk in response:
                await websocket.send_json(StreamResponse(
                    conversation_id=request.conversation_id or "new",
                    content=chunk,
                    model=response.metadata.get("model", settings.DEFAULT_CHAT_MODEL)
                ).dict())
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json(ErrorResponse(
            error="Internal Server Error",
            detail=str(e)
        ).dict())
        await websocket.close()

@router.get("/models", response_model=List[ModelInfo])
async def list_models(
    ollama_service: OllamaService = Depends(get_ollama_service)
) -> List[ModelInfo]:
    """List available models."""
    try:
        models = await ollama_service.list_models()
        return [
            ModelInfo(
                name=model.name,
                type=model.type.value,
                description=model.description,
                parameters=model.parameters
            )
            for model in models
        ]
    except OllamaServiceError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/models/{model_name}", response_model=ModelInfo)
async def get_model_info(
    model_name: str,
    ollama_service: OllamaService = Depends(get_ollama_service)
) -> ModelInfo:
    """Get information about a specific model."""
    try:
        model = await ollama_service.get_model_info(model_name)
        if not model:
            raise HTTPException(
                status_code=404,
                detail=f"Model {model_name} not found"
            )
        
        return ModelInfo(
            name=model.name,
            type=model.type.value,
            description=model.description,
            parameters=model.parameters
        )
        
    except OllamaServiceError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service),
    ai_service: AIService = Depends(get_ai_service)
):
    """WebSocket endpoint for real-time communication."""
    try:
        await manager.connect(websocket, client_id)
        
        # Initialize conversation
        conversation = await conversation_service.create_conversation(client_id)
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Process message
                response = await ai_service.process_message(
                    message=message["content"],
                    conversation_id=conversation.id
                )
                
                # Send response
                await manager.send_message(
                    json.dumps(WebSocketMessage(
                        type="message",
                        content=response,
                        timestamp=datetime.now()
                    ).dict()),
                    client_id
                )
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                error_msg = f"Error processing message: {str(e)}"
                await manager.send_message(
                    json.dumps(WebSocketMessage(
                        type="error",
                        content=error_msg
                    ).dict()),
                    client_id
                )
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        manager.disconnect(client_id)
        try:
            await conversation_service.end_conversation(client_id)
        except:
            pass

@router.get("/models")
async def list_models(
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service)
):
    """List available AI models."""
    try:
        models = await ai_service.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing models: {str(e)}"
        )

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    ai_service: AIService = Depends(get_ai_service),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """Chat endpoint for sending messages."""
    try:
        # Get or create conversation
        conversation = await conversation_service.get_conversation(current_user.id)
        if not conversation:
            conversation = await conversation_service.create_conversation(current_user.id)
        
        # Process message
        response = await ai_service.process_message(
            message=message.content,
            conversation_id=conversation.id
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