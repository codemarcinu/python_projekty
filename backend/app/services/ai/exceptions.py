class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass

class ModelNotFoundError(AIServiceError):
    """Raised when a requested AI model is not found."""
    pass

class ProcessingError(AIServiceError):
    """Raised when there's an error processing a message."""
    pass

class RAGError(AIServiceError):
    """Base exception for RAG-related errors."""
    pass

class DocumentProcessingError(RAGError):
    """Raised when there's an error processing a document."""
    pass

class VectorStoreError(RAGError):
    """Raised when there's an error with the vector store."""
    pass

class AgentError(AIServiceError):
    """Raised when there's an error with the AI agent."""
    pass

class ToolExecutionError(AgentError):
    """Raised when there's an error executing an agent tool."""
    pass 