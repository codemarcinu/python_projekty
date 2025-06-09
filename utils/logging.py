import logging
import structlog
import time
import sys
import asyncio
from typing import Dict, Any
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = "app.log"):
    """
    Konfiguruje structured logging dla aplikacji.
    
    Args:
        log_level: Poziom logowania (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Ścieżka do pliku logów
    """
    # Utwórz katalog logów jeśli nie istnieje
    log_path = Path(log_file).parent
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Konfiguracja formatowania logów
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Konfiguracja handlerów
    handlers = [
        # Handler do pliku
        logging.FileHandler(log_file),
        # Handler do konsoli
        logging.StreamHandler(sys.stdout)
    ]
    
    # Skonfiguruj root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Dodaj handlery
    for handler in handlers:
        handler.setFormatter(logging.Formatter('%(message)s'))
        root_logger.addHandler(handler)
    
    # Zwróć logger
    return structlog.get_logger()

# Tworzenie loggera
logger = setup_logging()

def log_execution_time(logger=logger):
    """
    Dekorator do logowania czasu wykonania funkcji.
    
    Args:
        logger: Logger do użycia
    """
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    "function_execution",
                    function=func.__name__,
                    execution_time=execution_time,
                    status="success"
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    "function_execution",
                    function=func.__name__,
                    execution_time=execution_time,
                    status="error",
                    error=str(e)
                )
                raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.info(
                    "function_execution",
                    function=func.__name__,
                    execution_time=execution_time,
                    status="success"
                )
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(
                    "function_execution",
                    function=func.__name__,
                    execution_time=execution_time,
                    status="error",
                    error=str(e)
                )
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator 