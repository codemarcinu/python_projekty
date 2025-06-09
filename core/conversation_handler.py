"""
Conversation handler for managing chat history and context.
Provides functionality for storing and retrieving conversation history.
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    filename='logs/conversation.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    
    # Maximum number of messages to keep in history
    MAX_MESSAGES = 100
    
    def add_message(self, role: str, content: str) -> None:
        """Add a new message to the conversation."""
        # Add new message
        self.messages.append(Message(role=role, content=content))
        self.updated_at = datetime.now()
        
        # Trim history if needed
        if len(self.messages) > self.MAX_MESSAGES:
            # Keep the first message (system prompt if exists) and the most recent messages
            first_message = self.messages[0]
            recent_messages = self.messages[-self.MAX_MESSAGES+1:]
            self.messages = [first_message] + recent_messages
            
            logger.info(f"Trimmed conversation {self.id} history to {len(self.messages)} messages")
    
    def get_context(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get conversation context in a format suitable for LLM."""
        # Ensure max_messages doesn't exceed MAX_MESSAGES
        max_messages = min(max_messages, self.MAX_MESSAGES)
        
        # Get recent messages
        recent_messages = self.messages[-max_messages:]
        return [{"role": msg.role, "content": msg.content} for msg in recent_messages]


class ConversationManager:
    """Manager for handling multiple conversations."""
    
    def __init__(self):
        """Initialize the conversation manager."""
        self._conversations: Dict[str, Conversation] = {}
        self._conversation_dir = Path("data/conversations")
        self._conversation_dir.mkdir(parents=True, exist_ok=True)
    
    def create_conversation(self, conversation_id: str) -> Conversation:
        """Create a new conversation."""
        if conversation_id in self._conversations:
            raise ValueError(f"Conversation with ID {conversation_id} already exists")
        
        conversation = Conversation(id=conversation_id)
        self._conversations[conversation_id] = conversation
        
        # Save conversation to disk
        self._save_conversation(conversation)
        
        logger.info(f"Created new conversation: {conversation_id}")
        return conversation
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        # Check memory first
        if conversation_id in self._conversations:
            return self._conversations[conversation_id]
        
        # Try to load from disk
        conversation_path = self._conversation_dir / f"{conversation_id}.json"
        if conversation_path.exists():
            try:
                conversation = Conversation.parse_file(conversation_path)
                self._conversations[conversation_id] = conversation
                logger.info(f"Loaded conversation from disk: {conversation_id}")
                return conversation
            except Exception as e:
                logger.error(f"Error loading conversation {conversation_id}: {str(e)}")
        
        return None
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation by ID."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            
            # Delete from disk
            conversation_path = self._conversation_dir / f"{conversation_id}.json"
            if conversation_path.exists():
                conversation_path.unlink()
            
            logger.info(f"Deleted conversation: {conversation_id}")
            return True
        return False
    
    def list_conversations(self) -> List[Tuple[str, str, datetime]]:
        """List all conversations with their IDs, titles, and last update times."""
        return [
            (conv.id, conv.title, conv.updated_at)
            for conv in self._conversations.values()
        ]
    
    def _save_conversation(self, conversation: Conversation) -> None:
        """Save a conversation to disk."""
        try:
            conversation_path = self._conversation_dir / f"{conversation.id}.json"
            conversation_path.write_text(conversation.json())
            logger.debug(f"Saved conversation to disk: {conversation.id}")
        except Exception as e:
            logger.error(f"Error saving conversation {conversation.id}: {str(e)}")
    
    def cleanup_old_conversations(self, max_age_days: int = 30) -> None:
        """Remove conversations older than max_age_days."""
        now = datetime.now()
        to_delete = []
        
        for conv_id, conv in self._conversations.items():
            age = now - conv.updated_at
            if age.days > max_age_days:
                to_delete.append(conv_id)
        
        for conv_id in to_delete:
            self.delete_conversation(conv_id)
        
        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} old conversations")


# Create global conversation manager instance
conversation_manager = ConversationManager()

def get_conversation_manager() -> ConversationManager:
    """Get the global conversation manager instance."""
    return conversation_manager
