from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from .base import BaseSchema

class TagBase(BaseModel):
    """Base tag schema."""
    name: str
    meta: Optional[Dict[str, Any]] = None

class TagCreate(TagBase):
    """Schema for creating a tag."""
    pass

class TagUpdate(BaseModel):
    """Schema for updating a tag."""
    name: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class Tag(TagBase, BaseSchema):
    """Schema for tag."""
    id: str
    user_id: str 