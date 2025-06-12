from datetime import datetime
from typing import Any
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import Column, BigInteger, DateTime
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base class for all models."""
    
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    created_at = Column(BigInteger, nullable=False, default=lambda: int(datetime.now().timestamp()))
    updated_at = Column(BigInteger, nullable=False, default=lambda: int(datetime.now().timestamp()), onupdate=lambda: int(datetime.now().timestamp()))
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns} 