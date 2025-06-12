"""
Moduł zarządzania logami.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from core.config import get_settings

class CustomFormatter(logging.Formatter):
    """Niestandardowy formatter logów."""
    
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: grey + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """Konfiguruje logger.
    
    Args:
        name: Nazwa loggera
        level: Poziom logowania
        log_file: Ścieżka do pliku logów (opcjonalnie)
        
    Returns:
        logging.Logger: Skonfigurowany logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Handler dla konsoli
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(CustomFormatter())
    logger.addHandler(console_handler)
    
    # Handler dla pliku
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(file_handler)
        
    return logger

def get_logger(name: str) -> logging.Logger:
    """Zwraca logger dla podanego modułu.
    
    Args:
        name: Nazwa modułu
        
    Returns:
        logging.Logger: Logger dla modułu
    """
    settings = get_settings()
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"{name}.log"
    
    return setup_logger(
        name=name,
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        log_file=str(log_file)
    )

# Przykład użycia:
# logger = get_logger(__name__)
# logger.info("Test message")
# logger.error("Error message")
# logger.warning("Warning message")
# logger.debug("Debug message") 