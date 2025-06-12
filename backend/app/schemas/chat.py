from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from .base import BaseSchema
from .user import User
from .message import Message
from .tag import Tag
from datetime import datetime

class ChatBase(BaseModel):
    """Base chat schema."""
    title: str
    chat: Dict[str, Any]
    meta: Optional[Dict[str, Any]] = None
    folder_id: Optional[str] = None

class ChatCreate(ChatBase):
    """Schema for creating a chat."""
    pass

class ChatUpdate(BaseModel):
    """Schema for updating a chat."""
    title: Optional[str] = None
    chat: Optional[Dict[str, Any]] = None
    meta: Optional[Dict[str, Any]] = None
    folder_id: Optional[str] = None
    archived: Optional[bool] = None
    pinned: Optional[bool] = None

class ChatInDB(ChatBase, BaseSchema):
    """Schema for chat in database."""
    id: str
    user_id: str
    share_id: Optional[str] = None
    archived: bool = False
    pinned: bool = False

class Chat(ChatInDB):
    """Schema for chat response."""
    user: Optional[User] = None
    messages: List[Message] = []
    tags: List[Tag] = []

class ChatMessage(BaseModel):
    content: str
    role: str
    timestamp: Optional[datetime] = None

class ChatResponse(BaseModel):
    message: str
    timestamp: datetime

class WebSocketMessage(BaseModel):
    type: str
    content: str
    timestamp: Optional[datetime] = None 