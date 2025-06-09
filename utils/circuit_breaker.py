from enum import Enum
from typing import Callable, Any, Optional, Type, Tuple
import time
import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "CLOSED"  # Normalny stan, zapytania są wykonywane
    OPEN = "OPEN"      # Stan awaryjny, zapytania są blokowane
    HALF_OPEN = "HALF_OPEN"  # Stan przejściowy, pozwala na testowe zapytania

class CircuitBreaker:
    """Implementacja wzorca Circuit Breaker."""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        expected_exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """
        Args:
            name: Nazwa circuit breakera
            failure_threshold: Liczba błędów po której circuit zostanie otwarty
            recovery_timeout: Czas w sekundach po którym circuit przejdzie w stan HALF_OPEN
            expected_exceptions: Typy wyjątków które są traktowane jako błędy
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self._lock = asyncio.Lock()
    
    async def __call__(self, func: Callable, *args, **kwargs) -> Any:
        """
        Wykonuje funkcję zgodnie z logiką Circuit Breaker.
        
        Args:
            func: Funkcja do wykonania
            *args: Argumenty pozycyjne
            **kwargs: Argumenty nazwane
            
        Returns:
            Wynik funkcji
            
        Raises:
            CircuitOpenError: Gdy circuit jest otwarty
            Exception: Oryginalny wyjątek z funkcji
        """
        async with self._lock:
            if self.state == CircuitState.OPEN:
                # Sprawdź czy minął czas recovery
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    logger.info(f"Circuit {self.name} switching to HALF_OPEN state")
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise CircuitOpenError(f"Circuit {self.name} is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            
            # Jeśli operacja się powiodła, zresetuj licznik błędów
            async with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    logger.info(f"Circuit {self.name} switching to CLOSED state")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    
            return result
            
        except self.expected_exceptions as e:
            # Obsłuż błąd
            async with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                # Jeśli osiągnięto próg błędów, otwórz circuit
                if (self.state == CircuitState.CLOSED and 
                    self.failure_count >= self.failure_threshold):
                    logger.warning(f"Circuit {self.name} switching to OPEN state")
                    self.state = CircuitState.OPEN
                    
            raise e

class CircuitOpenError(Exception):
    """Wyjątek rzucany, gdy circuit jest otwarty."""
    pass

def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 30,
    expected_exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Dekorator implementujący Circuit Breaker.
    
    Args:
        name: Nazwa circuit breakera
        failure_threshold: Liczba błędów po której circuit zostanie otwarty
        recovery_timeout: Czas w sekundach po którym circuit przejdzie w stan HALF_OPEN
        expected_exceptions: Typy wyjątków które są traktowane jako błędy
    """
    breaker = CircuitBreaker(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        expected_exceptions=expected_exceptions
    )
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker(func, *args, **kwargs)
        return wrapper
    
    return decorator 