"""
Moduł implementujący kontener wstrzykiwania zależności dla aplikacji.
"""

from dependency_injector import containers, providers
from core.config_manager import ConfigManager
from core.llm_manager import LLMManager
from core.rag_manager import RAGManager
from core.ai_engine import AIEngine
from core.config_manager import get_settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Container(containers.DeclarativeContainer):
    """Kontener wstrzykiwania zależności."""
    
    # Konfiguracja
    config = providers.Configuration()
    
    # Menedżer konfiguracji
    config_manager = providers.Singleton(
        ConfigManager,
        config=config
    )
    
    # Menedżer LLM
    llm_manager = providers.Singleton(
        LLMManager,
        config=config_manager
    )
    
    # Menedżer RAG
    rag_manager = providers.Singleton(
        RAGManager,
        config=config_manager
    )
    
    # Silnik AI
    ai_engine = providers.Singleton(
        AIEngine,
        llm_manager=llm_manager,
        rag_manager=rag_manager,
        config=config_manager
    ) 