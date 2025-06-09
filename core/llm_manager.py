"""
LLM Manager for handling language model interactions.
Provides a unified interface for different LLM providers.
"""
from typing import Any, Optional, cast
from datetime import datetime
import asyncio
import logging
import aiohttp
from pathlib import Path

from langchain_ollama import OllamaLLM
from langchain_core.language_models import BaseLLM
from langchain_core.callbacks import CallbackManagerForLLMRun

from .config_manager import get_settings
from .exceptions import ModelUnavailableError

# Configure logging
logger = logging.getLogger(__name__)

class LLMManager:
    """Manager for handling LLM interactions."""
    
    def __init__(self):
        """Initialize the LLM manager."""
        self.settings = get_settings()
        self._llm: Optional[BaseLLM] = None
        self._last_error_time: Optional[datetime] = None
        self._error_count = 0
        self._initialize_llm()
    
    def _initialize_llm(self) -> None:
        """Initialize the LLM with proper configuration."""
        try:
            if self.settings.llm.provider.lower() == "ollama":
                self._llm = OllamaLLM(
                    model=self.settings.llm.model_name,
                    base_url=self.settings.llm.ollama_host,
                    temperature=self.settings.llm.temperature
                )
                logger.info(f"Initialized Ollama LLM with model {self.settings.llm.model_name}")
            else:
                raise ValueError(f"Unsupported LLM provider: {self.settings.llm.provider}")
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            raise ModelUnavailableError(f"Failed to initialize LLM: {e}")
    
    @property
    def llm(self) -> BaseLLM:
        """Get the configured LLM instance."""
        if self._llm is None:
            self._initialize_llm()
        return cast(BaseLLM, self._llm)  # We know it's not None after initialization
    
    def get_health_status(self) -> dict:
        """Get the health status of the LLM."""
        return {
            "provider": self.settings.llm.provider,
            "model": self.settings.llm.model_name,
            "last_error": self._last_error_time.isoformat() if self._last_error_time else None,
            "error_count": self._error_count,
            "status": "healthy" if self._llm is not None else "unhealthy"
        }
    
    async def validate_ollama_model(self) -> None:
        """
        Validate that Ollama server is running and the required model is available.
        Raises ModelUnavailableError with a user-friendly message if not.
        """
        host = self.settings.llm.ollama_host.rstrip("/")
        model = self.settings.llm.model_name
        tags_url = f"{host}/api/tags"
        
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(tags_url) as resp:
                    if resp.status != 200:
                        raise ModelUnavailableError(f"Ollama API not available at {host} (status {resp.status})")
                    data = await resp.json()
                    available_models = [m['name'] for m in data.get('models', [])]
                    if model not in available_models:
                        raise ModelUnavailableError(
                            f"Model '{model}' is not available in Ollama. Dostępne modele: {', '.join(available_models) if available_models else 'brak'}. "
                            f"Użyj 'ollama pull {model}' lub zmień PRIMARY_MODEL w .env."
                        )
        except aiohttp.ClientError as e:
            logger.error(f"Ollama validation error: {e}")
            raise ModelUnavailableError(f"Nie można połączyć z Ollama ({host}). Szczegóły: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during Ollama validation: {e}")
            raise ModelUnavailableError(f"Nieoczekiwany błąd podczas walidacji Ollama: {e}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 3,
        **kwargs: Any
    ) -> str:
        """
        Generate text using the LLM with retry mechanism.
        
        Args:
            prompt: The input prompt for generation
            system_prompt: Optional system prompt to guide the model
            max_retries: Maximum number of retry attempts
            **kwargs: Additional arguments to pass to the LLM
            
        Returns:
            Generated text response
            
        Raises:
            ModelUnavailableError: If model is unavailable after retries
            asyncio.TimeoutError: If generation takes too long
        """
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt must be a non-empty string")
            
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting generation (attempt {attempt + 1}/{max_retries})")
                async with asyncio.timeout(self.settings.llm.timeout):
                    response = await self.llm.agenerate([full_prompt], **kwargs)
                    self._error_count = 0  # Reset error count on success
                    return response.generations[0][0].text
                
            except asyncio.TimeoutError:
                logger.error(f"Generation timeout after {self.settings.llm.timeout} seconds")
                self._last_error_time = datetime.now()
                self._error_count += 1
                
                if attempt == max_retries - 1:
                    raise ModelUnavailableError(
                        f"Model timeout after {max_retries} attempts"
                    )
                
                # Exponential backoff
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                self._last_error_time = datetime.now()
                self._error_count += 1
                logger.error(f"Generation error (attempt {attempt + 1}): {str(e)}")
                
                if attempt == max_retries - 1:
                    raise ModelUnavailableError(
                        f"Model unavailable after {max_retries} attempts. Last error: {str(e)}"
                    )
                
                # Exponential backoff
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        # This line should never be reached due to the raise in the loop
        raise ModelUnavailableError("Unexpected error in generate method")

    async def get_model_status(self) -> dict:
        """Get the current status of the LLM model.
        
        Returns:
            dict: Dictionary containing model status information:
                - model: Name of the current model
                - status: Current status ("online" or "offline")
        """
        try:
            await self.validate_ollama_model()
            return {
                "model": self.settings.llm.model_name,
                "status": "online"
            }
        except ModelUnavailableError:
            return {
                "model": self.settings.llm.model_name,
                "status": "offline"
            }

# Create global LLM manager instance
llm_manager = LLMManager()

def get_llm_manager() -> LLMManager:
    """Get the global LLM manager instance."""
    return llm_manager
