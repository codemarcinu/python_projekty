from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from .base import BaseSchema
from .user import User

class MessageReactionBase(BaseModel):
    """Base message reaction schema."""
    name: str

class MessageReactionCreate(MessageReactionBase):
    """Schema for creating a message reaction."""
    pass

class MessageReaction(MessageReactionBase, BaseSchema):
    """Schema for message reaction."""
    id: str
    message_id: str
    user_id: str
    user: Optional[User] = None

class MessageBase(BaseModel):
    """Base message schema."""
    content: str
    role: str
    meta: Optional[Dict[str, Any]] = None

class MessageCreate(MessageBase):
    """Schema for creating a message."""
    pass

class MessageUpdate(BaseModel):
    """Schema for updating a message."""
    content: Optional[str] = None
    role: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class Message(MessageBase, BaseSchema):
    """Schema for message."""
    id: str
    chat_id: str
    user_id: str
    user: Optional[User] = None
    reactions: List[MessageReaction] = [] 