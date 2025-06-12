class OllamaServiceError(Exception):
    """Base exception for Ollama service errors."""
    pass

class OllamaConnectionError(OllamaServiceError):
    """Raised when there's an error connecting to Ollama."""
    pass

class ModelNotFoundError(OllamaServiceError):
    """Raised when a requested model is not found."""
    pass

class ModelLoadError(OllamaServiceError):
    """Raised when there's an error loading a model."""
    pass

class GenerationError(OllamaServiceError):
    """Raised when there's an error during text generation."""
    pass

class EmbeddingError(OllamaServiceError):
    """Raised when there's an error generating embeddings."""
    pass

class ResourceLimitError(OllamaServiceError):
    """Raised when resource limits are exceeded."""
    pass

class ContextError(OllamaServiceError):
    """Raised when there's an error with conversation context."""
    pass 