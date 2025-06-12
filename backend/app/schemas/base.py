from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict

class BaseSchema(BaseModel):
    """Base schema for all models."""
    
    model_config = ConfigDict(from_attributes=True)
    
    created_at: int
    updated_at: int
    
    def to_dict(self) -> dict[str, Any]:
        """Convert schema to dictionary."""
        return self.model_dump() 