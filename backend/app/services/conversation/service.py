import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json

from pydantic import BaseModel, Field

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
    MAX_MESSAGES: int = 100

class ConversationService:
    """Service for managing conversations with proper error handling."""
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize the conversation service."""
        self._conversations: Dict[str, Conversation] = {}
        self._conversation_dir = Path(storage_path or "data/conversations")
        self._conversation_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_conversation(self, conversation_id: str) -> Conversation:
        """Create a new conversation."""
        try:
            if conversation_id in self._conversations:
                raise ValueError(f"Conversation with ID {conversation_id} already exists")
            
            conversation = Conversation(id=conversation_id)
            self._conversations[conversation_id] = conversation
            
            # Save conversation to disk
            await self._save_conversation(conversation)
            
            logger.info(f"Created new conversation: {conversation_id}")
            return conversation
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            raise
    
    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        try:
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
        except Exception as e:
            logger.error(f"Error getting conversation: {e}")
            raise
    
    async def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """Add a message to a conversation."""
        try:
            conversation = await self.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            
            # Add new message
            conversation.messages.append(Message(role=role, content=content))
            conversation.updated_at = datetime.now()
            
            # Trim history if needed
            if len(conversation.messages) > conversation.MAX_MESSAGES:
                # Keep the first message (system prompt if exists) and the most recent messages
                first_message = conversation.messages[0]
                recent_messages = conversation.messages[-conversation.MAX_MESSAGES+1:]
                conversation.messages = [first_message] + recent_messages
                
                logger.info(f"Trimmed conversation {conversation_id} history to {len(conversation.messages)} messages")
            
            # Save to disk
            await self._save_conversation(conversation)
            
        except Exception as e:
            logger.error(f"Error adding message to conversation {conversation_id}: {e}")
            raise
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation by ID."""
        try:
            if conversation_id in self._conversations:
                del self._conversations[conversation_id]
                
                # Delete from disk
                conversation_path = self._conversation_dir / f"{conversation_id}.json"
                if conversation_path.exists():
                    conversation_path.unlink()
                
                logger.info(f"Deleted conversation: {conversation_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting conversation {conversation_id}: {e}")
            raise
    
    async def list_conversations(self) -> List[Tuple[str, str, datetime]]:
        """List all conversations with their IDs, titles, and last update times."""
        try:
            return [
                (conv.id, conv.title, conv.updated_at)
                for conv in self._conversations.values()
            ]
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            raise
    
    async def _save_conversation(self, conversation: Conversation) -> None:
        """Save a conversation to disk."""
        try:
            conversation_path = self._conversation_dir / f"{conversation.id}.json"
            conversation_path.write_text(conversation.json())
            logger.debug(f"Saved conversation to disk: {conversation.id}")
        except Exception as e:
            logger.error(f"Error saving conversation {conversation.id}: {str(e)}")
            raise
    
    async def cleanup_old_conversations(self, max_age_days: int = 30) -> None:
        """Remove conversations older than max_age_days."""
        try:
            now = datetime.now()
            to_delete = []
            
            for conv_id, conv in self._conversations.items():
                age = now - conv.updated_at
                if age.days > max_age_days:
                    to_delete.append(conv_id)
            
            for conv_id in to_delete:
                await self.delete_conversation(conv_id)
            
            if to_delete:
                logger.info(f"Cleaned up {len(to_delete)} old conversations")
        except Exception as e:
            logger.error(f"Error cleaning up old conversations: {e}")
            raise
    
    async def end_conversation(self, conversation_id: str) -> None:
        """End a conversation and save it to disk."""
        try:
            if conversation_id in self._conversations:
                conversation = self._conversations[conversation_id]
                await self._save_conversation(conversation)
                logger.info(f"Ended conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Error ending conversation {conversation_id}: {e}")
            raise 