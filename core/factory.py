from typing import Dict, Any, Type
from core.providers import LLMProvider, OllamaProvider
import logging

logger = logging.getLogger(__name__)

class LLMProviderFactory:
    """Fabryka dostawców LLM."""
    
    _providers: Dict[str, Type[LLMProvider]] = {
        "ollama": OllamaProvider,
        # Można dodać więcej dostawców w przyszłości
    }
    
    @classmethod
    def create(cls, provider_type: str, config: Dict[str, Any]) -> LLMProvider:
        """
        Tworzy instancję dostawcy LLM na podstawie typu i konfiguracji.
        
        Args:
            provider_type: Typ dostawcy ("ollama", "openai", itp.)
            config: Słownik z konfiguracją
            
        Returns:
            Skonfigurowana instancja LLMProvider
            
        Raises:
            ValueError: Jeśli podano nieobsługiwany typ dostawcy
        """
        provider_type = provider_type.lower()
        
        if provider_type not in cls._providers:
            raise ValueError(
                f"Nieobsługiwany typ dostawcy: {provider_type}. "
                f"Dostępne typy: {list(cls._providers.keys())}"
            )
        
        provider_class = cls._providers[provider_type]
        logger.info(f"Tworzenie dostawcy {provider_type} z konfiguracją: {config}")
        
        return provider_class(**config)
    
    @classmethod
    def register_provider(cls, provider_type: str, provider_class: Type[LLMProvider]) -> None:
        """
        Rejestruje nowy typ dostawcy LLM.
        
        Args:
            provider_type: Typ dostawcy
            provider_class: Klasa implementująca LLMProvider
        """
        if not issubclass(provider_class, LLMProvider):
            raise TypeError(f"Klasa {provider_class.__name__} musi dziedziczyć po LLMProvider")
        
        cls._providers[provider_type.lower()] = provider_class
        logger.info(f"Zarejestrowano nowy dostawca: {provider_type}") 