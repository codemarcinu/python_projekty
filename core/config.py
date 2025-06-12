"""
Moduł konfiguracji aplikacji.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
import os

class Settings(BaseSettings):
    """Główne ustawienia aplikacji."""
    
    # Podstawowe ustawienia
    APP_NAME: str = "AI Assistant"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    
    # API
    API_PREFIX: str = "/api"
    API_V1_STR: str = "/v1"
    
    # Serwer
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list = ["*"]
    CORS_HEADERS: list = ["*"]
    
    # Bezpieczeństwo
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Ollama
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_TIMEOUT: int = 300
    
    # Modele
    PRIMARY_MODEL: str = "gemma3:12b"
    DOCUMENT_MODEL: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q6_K"
    
    # Limity
    MAX_FILE_SIZE: int = 52428800  # 50MB
    MAX_CONVERSATION_LENGTH: int = 100
    REQUEST_TIMEOUT: int = 30
    
    # Ścieżki
    UPLOAD_DIR: Path = Path("./uploads")
    FAISS_INDEX_PATH: Path = Path("./data/faiss_index")
    
    # RAG
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    MAX_SEARCH_RESULTS: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Singleton instance
_settings: Optional[Settings] = None

def get_settings() -> Settings:
    """Zwraca instancję ustawień (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

def init_settings() -> None:
    """Inicjalizuje ustawienia i tworzy wymagane katalogi."""
    settings = get_settings()
    
    # Tworzenie katalogów
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.FAISS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Ustawianie zmiennych środowiskowych
    os.environ["OLLAMA_HOST"] = settings.OLLAMA_HOST
    os.environ["OLLAMA_TIMEOUT"] = str(settings.OLLAMA_TIMEOUT) 