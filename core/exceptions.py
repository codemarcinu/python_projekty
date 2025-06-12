"""
Moduł zawierający niestandardowe wyjątki używane w aplikacji.

Ten moduł definiuje wszystkie niestandardowe wyjątki używane w różnych
częściach aplikacji, zapewniając spójną obsługę błędów.
"""

from typing import Optional, Any, Dict
from fastapi import HTTPException, status

class BaseError(Exception):
    """Bazowa klasa dla wszystkich błędów aplikacji."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(BaseError):
    """Błąd walidacji."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )

class AuthenticationError(BaseError):
    """Błąd autentykacji."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )

class AuthorizationError(BaseError):
    """Błąd autoryzacji."""
    
    def __init__(
        self,
        message: str = "Not authorized",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )

class NotFoundError(BaseError):
    """Błąd - nie znaleziono zasobu."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )

class ConflictError(BaseError):
    """Błąd konfliktu."""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )

class RateLimitError(BaseError):
    """Błąd przekroczenia limitu zapytań."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details
        )

class ModelError(BaseError):
    """Błąd modelu AI."""
    
    def __init__(
        self,
        message: str = "Model error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )

class FileError(BaseError):
    """Błąd operacji na plikach."""
    
    def __init__(
        self,
        message: str = "File operation error",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )

def handle_error(error: Exception) -> HTTPException:
    """Konwertuje błąd aplikacji na HTTPException.
    
    Args:
        error: Błąd do obsłużenia
        
    Returns:
        HTTPException: Błąd HTTP
    """
    if isinstance(error, BaseError):
        return HTTPException(
            status_code=error.status_code,
            detail={
                "message": error.message,
                "details": error.details
            }
        )
        
    # Domyślny błąd
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "message": str(error),
            "details": {}
        }
    )

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