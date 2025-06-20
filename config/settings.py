from pydantic_settings import BaseSettings
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

class LLMSettings(BaseModel):
    """Ustawienia dla modeli językowych."""
    primary_model: str = "gemma3:12b"
    document_model: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q6_K"
    ollama_host: str = "http://localhost:11434"
    ollama_timeout: int = 300

class RAGSettings(BaseSettings):
    """Settings for RAG (Retrieval-Augmented Generation) system."""
    base_url: str = "http://localhost:11434"
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    index_path: Path = Path("data/faiss_index.bin")
    vector_db_path: Path = Path("data/vector_db")
    upload_dir: Path = Path("uploads")
    max_results: int = 5
    similarity_threshold: float = 0.7
    embedding_dimension: int = 384  # Dimension for all-MiniLM-L6-v2
    use_ollama_embeddings: bool = False  # Set to True to use Ollama embeddings instead of sentence-transformers

    class Config:
        env_prefix = "RAG_"
        case_sensitive = False

class Settings(BaseSettings):
    """Główne ustawienia aplikacji."""
    # Podstawowe ustawienia
    app_name: str = "AI Assistant"
    debug: bool = False
    
    # Limity
    max_file_size: int = 52428800  # 50MB
    max_conversation_length: int = 100
    request_timeout: int = 30
    
    # Ścieżki
    log_dir: Path = Path("logs")
    
    # Modele i RAG
    llm: LLMSettings = LLMSettings()
    rag: RAGSettings = RAGSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

def get_settings() -> Settings:
    """Zwraca instancję ustawień."""
    return Settings() 