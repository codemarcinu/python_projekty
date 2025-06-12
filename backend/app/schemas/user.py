from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr, ConfigDict
from .base import BaseSchema

class UserBase(BaseModel):
    """Base user schema."""
    name: str
    email: EmailStr
    role: str = "user"
    profile_image_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    info: Optional[Dict[str, Any]] = None

class UserCreate(UserBase):
    """Schema for creating a user."""
    pass

class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    profile_image_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    info: Optional[Dict[str, Any]] = None

class UserInDB(UserBase, BaseSchema):
    """Schema for user in database."""
    id: str
    api_key: Optional[str] = None
    oauth_sub: Optional[str] = None
    last_active_at: Optional[str] = None

class User(UserInDB):
    """Schema for user response."""
    pass 