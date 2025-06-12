from typing import Optional
from sqlalchemy import Column, String, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Document(Base):
    """Document model."""
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    collection_name = Column(String, nullable=False)
    name = Column(String, nullable=False)
    title = Column(Text, nullable=False)
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    meta = Column(JSON, nullable=True)
    access_control = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="documents")
    tags = relationship("Tag", secondary="document_tags", back_populates="documents") 