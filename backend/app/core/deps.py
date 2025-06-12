from typing import Generator, Optional
from fastapi import Depends
from app.core.config import get_settings
from app.services.conversation.service import ConversationService
from app.services.ai.service import AIService

def get_conversation_service() -> Generator[ConversationService, None, None]:
    """Get conversation service instance."""
    service = ConversationService()
    try:
        yield service
    finally:
        # Cleanup if needed
        pass

def get_ai_service(
    conversation_service: ConversationService = Depends(get_conversation_service)
) -> Generator[AIService, None, None]:
    """Get AI service instance with dependencies."""
    service = AIService(conversation_service=conversation_service)
    try:
        yield service
    finally:
        # Cleanup if needed
        pass 