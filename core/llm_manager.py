"""
Moduł zarządzający modelami LLM.
"""

import os
import logging
from typing import Dict, Any, Optional
import aiohttp
import asyncio
from langchain_community.llms import Ollama
from core.config_manager import Settings, get_settings

logger = logging.getLogger(__name__)

# Singleton instance
_llm_manager: Optional['LLMManager'] = None

def get_llm_manager() -> 'LLMManager':
    """
    Zwraca instancję menedżera LLM (singleton).
    
    Returns:
        LLMManager: Instancja menedżera LLM
    """
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager(get_settings())
    return _llm_manager

class LLMManager:
    """Menedżer modeli LLM."""
    
    def __init__(self, settings: Settings):
        """
        Inicjalizuje menedżera LLM.
        
        Args:
            settings: Ustawienia aplikacji
        """
        self.settings = settings
        self.base_url = settings.llm.ollama_host
        self.timeout = settings.llm.timeout
        self.model = settings.llm.model_name
        self.session: Optional[aiohttp.ClientSession] = None
        self.llm: Optional[Ollama] = None
    
    async def initialize_llm(self):
        """Inicjalizuje połączenie z modelem LLM."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                base_url=self.base_url,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
            
        # Inicjalizacja modelu
        try:
            async with self.session.post(
                "/api/pull",
                json={"name": self.model}
            ) as response:
                if response.status != 200:
                    raise Exception(f"Error pulling model: {response.status}")
                
                # Inicjalizacja obiektu Ollama
                self.llm = Ollama(
                    base_url=self.base_url,
                    model=self.model,
                    timeout=self.timeout
                )
                logger.info(f"Model {self.model} initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing model: {e}")
            raise
    
    async def cleanup(self):
        """Zamyka połączenie z modelem LLM."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Generuje odpowiedź na podstawie promptu.
        
        Args:
            prompt: Tekst wejściowy
            model: Opcjonalna nazwa modelu
            
        Returns:
            str: Wygenerowana odpowiedź
            
        Raises:
            Exception: W przypadku błędu generowania
        """
        if not self.session:
            await self.initialize_llm()
        
        if not self.session:
            raise Exception("Failed to initialize LLM session")
        
        try:
            async with self.session.post(
                "/api/generate",
                json={
                    "model": model or self.model,
                    "prompt": prompt,
                    "stream": False
                }
            ) as response:
                if response.status != 200:
                    raise Exception(f"Error generating response: {response.status}")
                
                result = await response.json()
                return result.get("response", "")
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Sprawdza status modelu LLM.
        
        Returns:
            Dict[str, Any]: Status modelu
        """
        return {
            "model": self.model,
            "status": "connected" if self.session else "disconnected"
        }
