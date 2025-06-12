from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from .base import BaseSchema
from .user import User
from .tag import Tag

class DocumentBase(BaseModel):
    """Base document schema."""
    collection_name: str
    name: str
    title: str
    filename: str
    content: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    access_control: Optional[Dict[str, Any]] = None

class DocumentCreate(DocumentBase):
    """Schema for creating a document."""
    pass

class DocumentUpdate(BaseModel):
    """Schema for updating a document."""
    collection_name: Optional[str] = None
    name: Optional[str] = None
    title: Optional[str] = None
    filename: Optional[str] = None
    content: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None
    access_control: Optional[Dict[str, Any]] = None

class DocumentInDB(DocumentBase, BaseSchema):
    """Schema for document in database."""
    id: str
    user_id: str

class Document(DocumentInDB):
    """Schema for document response."""
    user: Optional[User] = None
    tags: List[Tag] = [] 