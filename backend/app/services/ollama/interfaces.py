from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from enum import Enum

class ModelType(Enum):
    """Types of Ollama models."""
    CHAT = "chat"
    EMBEDDING = "embedding"
    CODE = "code"

class ModelInfo:
    """Information about an Ollama model."""
    name: str
    type: ModelType
    description: str
    parameters: Dict[str, Any]
    last_used: Optional[datetime] = None
    performance_metrics: Dict[str, float] = {}

class OllamaServiceInterface(ABC):
    """Interface for Ollama service operations."""
    
    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """List available Ollama models."""
        pass
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model_name: str,
        stream: bool = False,
        **kwargs
    ) -> AsyncGenerator[str, None] | str:
        """Generate text using specified model."""
        pass
    
    @abstractmethod
    async def generate_with_context(
        self,
        prompt: str,
        model_name: str,
        context: List[Dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> AsyncGenerator[str, None] | str:
        """Generate text with conversation context."""
        pass
    
    @abstractmethod
    async def get_embeddings(
        self,
        text: str,
        model_name: str = "nomic-embed-text:latest"
    ) -> List[float]:
        """Get embeddings for text."""
        pass
    
    @abstractmethod
    async def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        pass
    
    @abstractmethod
    async def get_performance_metrics(self, model_name: str) -> Dict[str, float]:
        """Get performance metrics for a model."""
        pass 