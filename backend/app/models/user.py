from typing import Optional
from sqlalchemy import Column, String, Text, JSON
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    """User model."""
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    role = Column(String, nullable=False, default="user")
    profile_image_url = Column(Text, nullable=True)
    
    last_active_at = Column(String, nullable=True)
    api_key = Column(String, nullable=True, unique=True)
    settings = Column(JSON, nullable=True)
    info = Column(JSON, nullable=True)
    oauth_sub = Column(Text, nullable=True, unique=True)
    
    # Relationships
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    folders = relationship("Folder", back_populates="user", cascade="all, delete-orphan") 