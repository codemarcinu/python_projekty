"""
Configuration manager for the AI Assistant.
Handles loading and validating configuration from environment variables and config files.
"""
import os
from pathlib import Path
from typing import Optional
import logging
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    filename='logs/config.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class LLMSettings(BaseModel):
    """Settings for LLM configuration."""
    provider: str = Field(default="ollama", description="LLM provider (e.g., ollama, vllm)")
    model_name: str = Field(default="llama2", description="Name of the LLM model to use")
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama API host")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0, description="Temperature for text generation")
    timeout: int = Field(default=300, gt=0, description="Timeout in seconds for LLM operations")
    max_tokens: int = Field(default=2000, gt=0, description="Maximum tokens in response")
    context_window: int = Field(default=4096, gt=0, description="Context window size")

class RAGSettings(BaseModel):
    """Settings for RAG system configuration."""
    vector_db_path: Path = Field(default=Path("data/vector_db"), description="Path to vector database")
    chunk_size: int = Field(default=1000, gt=0, description="Size of text chunks for processing")
    chunk_overlap: int = Field(default=200, ge=0, description="Overlap between chunks")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Model for text embeddings")

class Settings(BaseModel):
    """Main settings class for the application."""
    # Security settings
    api_key: str = Field(default="", description="API key for authentication")
    
    # Database settings
    db_path: Path = Field(default=Path("data/assistant.db"), description="Path to SQLite database")
    
    # Component settings
    llm: LLMSettings = Field(default_factory=LLMSettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)
    
    # Logging settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_dir: Path = Field(default=Path("logs"), description="Directory for log files")
    
    # File storage settings
    upload_dir: Path = Field(default=Path("uploads"), description="Directory for uploaded files")
    max_file_size: int = Field(default=50 * 1024 * 1024, gt=0, description="Maximum file size in bytes")
    
    # Rate limiting settings
    rate_limit_window: int = Field(default=3600, gt=0, description="Rate limit window in seconds")
    max_requests_per_window: int = Field(default=100, gt=0, description="Maximum requests per window")
    
    # Conversation settings
    max_conversation_age_days: int = Field(default=30, gt=0, description="Maximum age of conversations in days")
    max_messages_per_conversation: int = Field(default=100, gt=0, description="Maximum messages per conversation")
    
    @validator('api_key')
    def validate_api_key(cls, v):
        """Validate API key is set."""
        if not v:
            logger.warning("API key not set. This is not recommended for production use.")
        return v
    
    @validator('log_dir', 'upload_dir')
    def create_directories(cls, v):
        """Create required directories."""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {', '.join(valid_levels)}")
        return v.upper()

def get_settings() -> Settings:
    """Get the application settings."""
    try:
        settings = Settings()
        logger.info("Configuration loaded successfully")
        return settings
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise

# Create global settings instance
settings = get_settings()

class ConfigManager:
    """Manager for configuration and environment variables."""
    
    @staticmethod
    def get_secret(key: str) -> str:
        """
        Get a secret value from environment variables.
        
        Args:
            key: The environment variable key to retrieve.
            
        Returns:
            The value of the environment variable.
            
        Raises:
            ValueError: If the environment variable is not found.
        """
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Environment variable '{key}' not found")
        return value
