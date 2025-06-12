from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, validator, Field
import secrets
from pathlib import Path

class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Chat API"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "python_projekty"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict[str, any]) -> any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT: int = 30
    OLLAMA_MAX_RETRIES: int = 3
    OLLAMA_RETRY_DELAY: float = 1.0
    OLLAMA_MAX_CONTEXT_LENGTH: int = 4096
    OLLAMA_MAX_TOKENS: int = 2048
    OLLAMA_TEMPERATURE: float = 0.7
    OLLAMA_TOP_P: float = 0.9
    OLLAMA_TOP_K: int = 40
    OLLAMA_REPEAT_PENALTY: float = 1.1
    OLLAMA_STOP_SEQUENCES: List[str] = Field(default_factory=list)
    OLLAMA_RESOURCE_LIMITS: Dict[str, float] = Field(
        default_factory=lambda: {
            "cpu_percent": 90.0,
            "memory_percent": 90.0,
            "gpu_memory_percent": 90.0
        }
    )
    
    # RAG
    RAG_EMBEDDING_MODEL: str = "llama2"
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    
    # File Storage
    UPLOAD_DIR: Path = Path("uploads")
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Default models
    DEFAULT_CHAT_MODEL: str = "mistral:latest"
    DEFAULT_CODE_MODEL: str = "deepseek-coder-v2:latest"
    DEFAULT_EMBEDDING_MODEL: str = "nomic-embed-text:latest"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 