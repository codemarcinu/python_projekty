"""
Conversation handler for managing chat history and context.
Provides functionality for storing and retrieving conversation history.
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a single message in a conversation."""
    role: str = Field(..., description="Role of the message sender (user/assistant/system)")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")


class Conversation(BaseModel):
    """Represents a complete conversation with history."""
    id: str = Field(..., description="Unique conversation identifier")
    title: str = Field(default="New Conversation", description="Conversation title")
    messages: List[Message] = Field(default_factory=list, description="List of messages")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    def add_message(self, role: str, content: str) -> None:
        """Add a new message to the conversation."""
        self.messages.append(Message(role=role, content=content))
        self.updated_at = datetime.now()
    
    def get_context(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get conversation context in a format suitable for LLM."""
        recent_messages = self.messages[-max_messages:]
        return [{"role": msg.role, "content": msg.content} for msg in recent_messages]


class ConversationManager:
    """Manager for handling multiple conversations."""
    
    def __init__(self):
        """Initialize the conversation manager."""
        self._conversations: Dict[str, Conversation] = {}
    
    def create_conversation(self, conversation_id: str) -> Conversation:
        """Create a new conversation."""
        if conversation_id in self._conversations:
            raise ValueError(f"Conversation with ID {conversation_id} already exists")
        
        conversation = Conversation(id=conversation_id)
        self._conversations[conversation_id] = conversation
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return self._conversations.get(conversation_id)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation by ID."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            return True
        return False
    
    def list_conversations(self) -> List[Tuple[str, str, datetime]]:
        """List all conversations with their IDs, titles, and last update times."""
        return [
            (conv.id, conv.title, conv.updated_at)
            for conv in self._conversations.values()
        ]


# Create global conversation manager instance
conversation_manager = ConversationManager()

def get_conversation_manager() -> ConversationManager:
    """Get the global conversation manager instance."""
    return conversation_manager
