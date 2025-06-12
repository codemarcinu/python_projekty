from typing import Optional
from sqlalchemy import Column, String, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Message(Base):
    """Message model."""
    
    id = Column(String, primary_key=True)
    chat_id = Column(String, ForeignKey("chat.id"), nullable=False)
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    content = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    meta = Column(JSON, nullable=True)
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")
    user = relationship("User")
    reactions = relationship("MessageReaction", back_populates="message", cascade="all, delete-orphan")

class MessageReaction(Base):
    """Message reaction model."""
    
    id = Column(String, primary_key=True)
    message_id = Column(String, ForeignKey("message.id"), nullable=False)
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    name = Column(Text, nullable=False)  # emoji or reaction name
    
    # Relationships
    message = relationship("Message", back_populates="reactions")
    user = relationship("User") 