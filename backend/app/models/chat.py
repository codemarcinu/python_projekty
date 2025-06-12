from typing import Optional
from sqlalchemy import Column, String, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Chat(Base):
    """Chat model."""
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    title = Column(Text, nullable=False)
    chat = Column(JSON, nullable=False)
    
    share_id = Column(Text, unique=True, nullable=True)
    archived = Column(Boolean, default=False)
    pinned = Column(Boolean, default=False)
    meta = Column(JSON, server_default="{}")
    folder_id = Column(Text, ForeignKey("folder.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="chats")
    folder = relationship("Folder", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="chat_tags", back_populates="chats") 