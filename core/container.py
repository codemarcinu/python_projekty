from dependency_injector import containers, providers
from core.llm_manager import LLMManager
from core.ai_engine import AIEngine
from core.rag_manager import RAGManager
from core.config_manager import get_settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Container(containers.DeclarativeContainer):
    """Kontener DI dla aplikacji."""
    
    config = providers.Configuration()
    
    # Konfiguracja z pliku .env
    config.ollama_host.from_env("OLLAMA_HOST", default="http://localhost:11434")
    config.ollama_timeout.from_env("OLLAMA_TIMEOUT", default=30)
    config.primary_model.from_env("PRIMARY_MODEL", default="gemma3:12b")
    config.document_model.from_env("DOCUMENT_MODEL", default="SpeakLeash/bielik-11b-v2.3-instruct:Q6_K")
    config.rag_embedding_model.from_env("RAG_EMBEDDING_MODEL", default="all-MiniLM-L6-v2")
    
    # Dostawcy usług
    llm_manager = providers.Singleton(
        LLMManager,
        base_url=config.ollama_host,
        timeout=config.ollama_timeout,
        model=config.primary_model
    )
    
    rag_manager = providers.Singleton(
        RAGManager,
        embedding_model=config.rag_embedding_model
    )
    
    ai_engine = providers.Singleton(
        AIEngine,
        llm_manager=llm_manager,
        rag_manager=rag_manager
    ) 