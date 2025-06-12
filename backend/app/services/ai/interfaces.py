from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime

class AIServiceInterface(ABC):
    """Interface for AI service operations."""
    
    @abstractmethod
    async def process_message(self, message: str, conversation_id: str) -> str:
        """Process a user message and return a response."""
        pass
    
    @abstractmethod
    async def list_models(self) -> List[str]:
        """List available AI models."""
        pass
    
    @abstractmethod
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and configuration."""
        pass

class RAGServiceInterface(ABC):
    """Interface for RAG (Retrieval Augmented Generation) operations."""
    
    @abstractmethod
    async def process_query(self, query: str, chat_history: str = "") -> str:
        """Process a query using RAG."""
        pass
    
    @abstractmethod
    async def add_document(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add a document to the vector store."""
        pass
    
    @abstractmethod
    async def search_documents(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents."""
        pass 