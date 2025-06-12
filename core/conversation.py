"""
Moduł zarządzania konwersacjami.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel
from datetime import datetime
import uuid
import logging
from core.llm_manager import LLMManager, ModelResponse

logger = logging.getLogger(__name__)

class Message(BaseModel):
    """Model wiadomości."""
    id: str
    role: str
    content: str
    timestamp: datetime
    model: Optional[str] = None
    error: Optional[str] = None

class Conversation(BaseModel):
    """Model konwersacji."""
    id: str
    title: str
    messages: List[Message]
    created_at: datetime
    updated_at: datetime
    model_id: str
    user_id: str

class ConversationManager:
    """Klasa zarządzająca konwersacjami."""
    
    def __init__(self, llm_manager: LLMManager):
        self.llm_manager = llm_manager
        self.conversations: Dict[str, Conversation] = {}
        
    def create_conversation(
        self,
        user_id: str,
        model_id: str,
        title: Optional[str] = None
    ) -> Conversation:
        """Tworzy nową konwersację."""
        conversation_id = str(uuid.uuid4())
        now = datetime.now()
        
        conversation = Conversation(
            id=conversation_id,
            title=title or f"New Conversation {now.strftime('%Y-%m-%d %H:%M')}",
            messages=[],
            created_at=now,
            updated_at=now,
            model_id=model_id,
            user_id=user_id
        )
        
        self.conversations[conversation_id] = conversation
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Pobiera konwersację."""
        return self.conversations.get(conversation_id)
    
    def get_user_conversations(self, user_id: str) -> List[Conversation]:
        """Pobiera konwersacje użytkownika."""
        return [
            conv for conv in self.conversations.values()
            if conv.user_id == user_id
        ]
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Usuwa konwersację."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False
    
    async def add_message(
        self,
        conversation_id: str,
        content: str,
        role: str = "user"
    ) -> Optional[Message]:
        """Dodaje wiadomość do konwersacji."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
            
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now()
        )
        
        conversation.messages.append(message)
        conversation.updated_at = datetime.now()
        
        return message
    
    async def generate_response(
        self,
        conversation_id: str,
        user_message: str
    ) -> Optional[Message]:
        """Generuje odpowiedź modelu na wiadomość użytkownika."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
            
        # Dodaj wiadomość użytkownika
        user_msg = await self.add_message(conversation_id, user_message, "user")
        if not user_msg:
            return None
            
        try:
            # Przygotuj kontekst z historii konwersacji
            context = "\n".join([
                f"{msg.role}: {msg.content}"
                for msg in conversation.messages[-5:]  # Ostatnie 5 wiadomości
            ])
            
            # Generuj odpowiedź
            response = await self.llm_manager.generate_response(
                prompt=context,
                model_id=conversation.model_id
            )
            
            # Dodaj odpowiedź do konwersacji
            assistant_msg = await self.add_message(
                conversation_id,
                response.content,
                "assistant"
            )
            
            if assistant_msg:
                assistant_msg.model = response.model
                if response.error:
                    assistant_msg.error = response.error
                    
            return assistant_msg
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            error_msg = await self.add_message(
                conversation_id,
                "Sorry, I encountered an error while processing your request.",
                "assistant"
            )
            if error_msg:
                error_msg.error = str(e)
            return error_msg 