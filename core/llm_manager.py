"""
Moduł zarządzający modelami LLM.
"""

import os
import logging
from typing import Dict, Any, Optional
import aiohttp
import asyncio
from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class LLMManager:
    """Menedżer modeli LLM."""
    
    def __init__(self, config: ConfigManager):
        """
        Inicjalizuje menedżera LLM.
        
        Args:
            config: Menedżer konfiguracji
        """
        self.config = config
        self.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.timeout = int(os.getenv("OLLAMA_TIMEOUT", "30"))
        self.model = os.getenv("PRIMARY_MODEL", "gemma3:12b")
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize_llm(self):
        """Inicjalizuje połączenie z modelem LLM."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                base_url=self.base_url,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
    
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
