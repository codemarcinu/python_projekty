from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime

class LLMResponse(BaseModel):
    """Model odpowiedzi z LLM."""
    content: str
    model: str
    tokens_used: int
    timestamp: datetime = datetime.now()

class LLMProvider(ABC):
    """Abstrakcyjna klasa bazowa dla dostawców modeli językowych."""
    
    @abstractmethod
    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        """Generuje odpowiedź na podstawie promptu."""
        pass
    
    @abstractmethod
    async def check_availability(self) -> bool:
        """Sprawdza dostępność modelu."""
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[str]:
        """Zwraca listę dostępnych modeli."""
        pass

class OllamaProvider(LLMProvider):
    """Implementacja LLMProvider dla Ollama."""
    
    def __init__(self, base_url: str, model: str, timeout: int = 30):
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        
    async def generate_response(self, prompt: str, **kwargs) -> LLMResponse:
        """Implementacja generowania odpowiedzi przez Ollama."""
        # TODO: Implementacja komunikacji z Ollama API
        raise NotImplementedError("OllamaProvider.generate_response not implemented")
        
    async def check_availability(self) -> bool:
        """Sprawdza dostępność modelu Ollama."""
        # TODO: Implementacja sprawdzania dostępności
        raise NotImplementedError("OllamaProvider.check_availability not implemented")
    
    async def get_available_models(self) -> List[str]:
        """Zwraca listę dostępnych modeli w Ollama."""
        # TODO: Implementacja pobierania listy modeli
        raise NotImplementedError("OllamaProvider.get_available_models not implemented") 