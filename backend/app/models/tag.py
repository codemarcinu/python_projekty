from typing import Optional
from sqlalchemy import Column, String, Text, JSON, Table, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

# Association tables
chat_tags = Table(
    "chat_tags",
    Base.metadata,
    Column("chat_id", String, ForeignKey("chat.id")),
    Column("tag_id", String, ForeignKey("tag.id"))
)

document_tags = Table(
    "document_tags",
    Base.metadata,
    Column("document_id", String, ForeignKey("document.id")),
    Column("tag_id", String, ForeignKey("tag.id"))
)

class Tag(Base):
    """Tag model."""
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    name = Column(String, nullable=False)
    meta = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User")
    chats = relationship("Chat", secondary=chat_tags, back_populates="tags")
    documents = relationship("Document", secondary=document_tags, back_populates="tags") 