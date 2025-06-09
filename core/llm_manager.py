"""
LLM Manager for handling interactions with Ollama models.
Provides a unified interface for text generation and embeddings.
"""
from typing import Any, Dict, List, Optional
import asyncio
import logging
from datetime import datetime

from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings

from .config_manager import get_settings

# Configure logging
logging.basicConfig(
    filename='logs/llm_manager.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass

class ModelUnavailableError(LLMError):
    """Raised when the model is unavailable after retries."""
    pass

class LLMManager:
    """Manager for handling LLM operations using Ollama."""
    
    def __init__(self):
        """Initialize the LLM manager with configuration from settings."""
        self.settings = get_settings()
        self._llm: Optional[Ollama] = None
        self._embeddings: Optional[OllamaEmbeddings] = None
        self._last_error_time: Optional[datetime] = None
        self._error_count = 0
        
    @property
    def llm(self) -> Ollama:
        """Get or create the LLM instance."""
        if self._llm is None:
            callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
            self._llm = Ollama(
                model=self.settings.llm.model_name,
                temperature=self.settings.llm.temperature,
                callback_manager=callback_manager
            )
        return self._llm
    
    @property
    def embeddings(self) -> OllamaEmbeddings:
        """Get or create the embeddings instance."""
        if self._embeddings is None:
            self._embeddings = OllamaEmbeddings(
                model=self.settings.rag.embedding_model
            )
        return self._embeddings
    
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
    
    async def get_embeddings(self, texts: List[str], max_retries: int = 3) -> List[List[float]]:
        """
        Get embeddings for a list of texts with retry mechanism.
        
        Args:
            texts: List of texts to embed
            max_retries: Maximum number of retry attempts
            
        Returns:
            List of embedding vectors
            
        Raises:
            ModelUnavailableError: If model is unavailable after retries
            asyncio.TimeoutError: If embedding generation takes too long
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting embeddings (attempt {attempt + 1}/{max_retries})")
                async with asyncio.timeout(self.settings.llm.timeout):
                    embeddings = await self.embeddings.aembed_documents(texts)
                    self._error_count = 0  # Reset error count on success
                    return embeddings
                
            except asyncio.TimeoutError:
                logger.error(f"Embeddings timeout after {self.settings.llm.timeout} seconds")
                self._last_error_time = datetime.now()
                self._error_count += 1
                
                if attempt == max_retries - 1:
                    raise ModelUnavailableError(
                        f"Embeddings model timeout after {max_retries} attempts"
                    )
                
                # Exponential backoff
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                self._last_error_time = datetime.now()
                self._error_count += 1
                logger.error(f"Embeddings error (attempt {attempt + 1}): {str(e)}")
                
                if attempt == max_retries - 1:
                    raise ModelUnavailableError(
                        f"Embeddings model unavailable after {max_retries} attempts. Last error: {str(e)}"
                    )
                
                # Exponential backoff
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        
        # This line should never be reached due to the raise in the loop
        raise ModelUnavailableError("Unexpected error in get_embeddings method")
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available Ollama models.
        
        Returns:
            List of model information dictionaries
        """
        # TODO: Implement model listing from Ollama API
        return []
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get the current health status of the LLM manager.
        
        Returns:
            Dictionary containing health metrics
        """
        return {
            "error_count": self._error_count,
            "last_error_time": self._last_error_time.isoformat() if self._last_error_time else None,
            "model_initialized": self._llm is not None,
            "embeddings_initialized": self._embeddings is not None
        }

# Create global LLM manager instance
llm_manager = LLMManager()

def get_llm_manager() -> LLMManager:
    """Get the global LLM manager instance."""
    return llm_manager
