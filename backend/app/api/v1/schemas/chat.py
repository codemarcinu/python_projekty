from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator

class MessageBase(BaseModel):
    """Base message schema."""
    content: str = Field(..., min_length=1, max_length=4000)
    role: str = Field(..., pattern="^(user|assistant|system)$")

class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    pass

class Message(MessageBase):
    """Schema for message response."""
    id: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        from_attributes = True

class ConversationBase(BaseModel):
    """Base conversation schema."""
    title: str = Field(..., min_length=1, max_length=100)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""
    initial_message: Optional[str] = Field(None, min_length=1, max_length=4000)

class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    metadata: Optional[Dict[str, Any]] = None

class Conversation(ConversationBase):
    """Schema for conversation response."""
    id: str
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    """Schema for chat request."""
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None
    stream: bool = Field(default=False)
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, gt=0, le=4000)

    @validator('temperature')
    def validate_temperature(cls, v):
        if v is not None and not 0 <= v <= 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v

class ChatResponse(BaseModel):
    """Schema for chat response."""
    conversation_id: str
    message: Message
    model: str
    usage: Dict[str, int]
    created: datetime = Field(default_factory=datetime.now)

class StreamResponse(BaseModel):
    """Schema for streaming response."""
    conversation_id: str
    content: str
    model: str
    created: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseModel):
    """Schema for error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None 