"""
Configuration manager for the AI Assistant application.
Handles loading and validation of application settings.
"""
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseModel):
    """Settings for LLM configuration."""
    provider: str = Field(default="ollama", description="LLM provider (e.g., ollama, vllm)")
    model_name: str = Field(default="llama2", description="Name of the model to use")
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama API host")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Temperature for model generation")
    max_tokens: int = Field(default=2000, gt=0, description="Maximum tokens in response")
    context_window: int = Field(default=4096, gt=0, description="Context window size")


class RAGSettings(BaseModel):
    """Settings for RAG system configuration."""
    vector_db_path: Path = Field(default=Path("data/vector_db"), description="Path to vector database")
    chunk_size: int = Field(default=1000, gt=0, description="Size of text chunks for processing")
    chunk_overlap: int = Field(default=200, ge=0, description="Overlap between chunks")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Model for text embeddings")


class WebSettings(BaseModel):
    """Settings for web interface configuration."""
    host: str = Field(default="127.0.0.1", description="Host for web interface")
    port: int = Field(default=8000, gt=0, lt=65536, description="Port for web interface")
    debug: bool = Field(default=False, description="Enable debug mode")


class Settings(BaseSettings):
    """Main application settings."""
    # Base settings
    app_name: str = Field(default="AI Assistant", description="Application name")
    version: str = Field(default="0.1.0", description="Application version")
    data_dir: Path = Field(default=Path("data"), description="Base directory for data storage")
    db_path: str = Field(default="data/assistant.db", description="Path to SQLite database")
    weather_api_key: str = Field(default="", description="API key for weather service")
    
    # Component settings
    llm: LLMSettings = Field(default_factory=lambda: LLMSettings())
    rag: RAGSettings = Field(default_factory=lambda: RAGSettings())
    web: WebSettings = Field(default_factory=lambda: WebSettings())
    
    # Security
    secret_key: str = Field(default="your-secret-key-here", description="Secret key for security")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=True
    )


# Create global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
