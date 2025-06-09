"""
Moduł zawierający niestandardowe wyjątki używane w aplikacji.

Ten moduł definiuje wszystkie niestandardowe wyjątki używane w różnych
częściach aplikacji, zapewniając spójną obsługę błędów.
"""

class AIEngineError(Exception):
    """Wyjątek występujący podczas pracy silnika AI."""
    pass


class ConversationError(Exception):
    """Wyjątek występujący podczas obsługi konwersacji."""
    pass


class DatabaseError(Exception):
    """Wyjątek występujący podczas operacji na bazie danych."""
    pass


class ConfigError(Exception):
    """Wyjątek występujący podczas obsługi konfiguracji."""
    pass


class ModelUnavailableError(AIEngineError):
    """Raised when the LLM model is unavailable or fails to respond."""
    pass


class ConfigurationError(AIEngineError):
    """Raised when there is a configuration error."""
    pass


class ValidationError(AIEngineError):
    """Raised when input validation fails."""
    pass 