"""
Moduł zarządzania modelami LLM.
"""

from typing import List, Optional, Dict, Any
import httpx
import asyncio
from pydantic import BaseModel
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ModelConfig(BaseModel):
    """Konfiguracja modelu."""
    id: str
    name: str
    description: str
    context_window: int
    max_tokens: int
    temperature: float = 0.7
    is_available: bool = True

class ModelResponse(BaseModel):
    """Odpowiedź modelu."""
    content: str
    model: str
    timestamp: datetime
    tokens_used: Optional[int] = None
    error: Optional[str] = None

class LLMManager:
    """Klasa zarządzająca modelami LLM."""
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_host = ollama_host
        self.models: Dict[str, ModelConfig] = {}
        self._client = httpx.AsyncClient(timeout=30.0)
        
    async def initialize(self):
        """Inicjalizuje menedżer modeli."""
        try:
            # Pobierz listę dostępnych modeli z Ollama
            response = await self._client.get(f"{self.ollama_host}/api/tags")
            if response.status_code == 200:
                models_data = response.json()
                for model in models_data.get("models", []):
                    self.models[model["name"]] = ModelConfig(
                        id=model["name"],
                        name=model["name"].split(":")[0],
                        description=f"Model {model['name']}",
                        context_window=4096,  # Domyślna wartość
                        max_tokens=2048,      # Domyślna wartość
                        is_available=True
                    )
            else:
                logger.error(f"Failed to fetch models: {response.status_code}")
        except Exception as e:
            logger.error(f"Error initializing LLM manager: {e}")
            
    async def get_available_models(self) -> List[ModelConfig]:
        """Zwraca listę dostępnych modeli."""
        return list(self.models.values())
    
    async def get_model(self, model_id: str) -> Optional[ModelConfig]:
        """Pobiera konfigurację modelu."""
        return self.models.get(model_id)
    
    async def generate_response(
        self,
        prompt: str,
        model_id: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ModelResponse:
        """Generuje odpowiedź modelu."""
        try:
            model = await self.get_model(model_id)
            if not model or not model.is_available:
                raise ValueError(f"Model {model_id} is not available")
                
            response = await self._client.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": model_id,
                    "prompt": prompt,
                    "temperature": temperature or model.temperature,
                    "max_tokens": max_tokens or model.max_tokens
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return ModelResponse(
                    content=result["response"],
                    model=model_id,
                    timestamp=datetime.now(),
                    tokens_used=result.get("tokens_used")
                )
            else:
                raise Exception(f"Model generation failed: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return ModelResponse(
                content="",
                model=model_id,
                timestamp=datetime.now(),
                error=str(e)
            )
    
    async def close(self):
        """Zamyka połączenia."""
        await self._client.aclose()
