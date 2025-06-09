"""
LLM Manager for handling interactions with Ollama models.
Provides a unified interface for text generation and embeddings.
"""
from typing import Any, Dict, List, Optional

from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings

from .config_manager import get_settings


class LLMManager:
    """Manager for handling LLM operations using Ollama."""
    
    def __init__(self):
        """Initialize the LLM manager with configuration from settings."""
        self.settings = get_settings()
        self._llm: Optional[Ollama] = None
        self._embeddings: Optional[OllamaEmbeddings] = None
        
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
        **kwargs: Any
    ) -> str:
        """
        Generate text using the LLM.
        
        Args:
            prompt: The input prompt for generation
            system_prompt: Optional system prompt to guide the model
            **kwargs: Additional arguments to pass to the LLM
            
        Returns:
            Generated text response
        """
        # Prepare the full prompt with system message if provided
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        # Generate response
        response = await self.llm.agenerate([full_prompt], **kwargs)
        return response.generations[0][0].text
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        return await self.embeddings.aembed_documents(texts)
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available Ollama models.
        
        Returns:
            List of model information dictionaries
        """
        # TODO: Implement model listing from Ollama API
        return []


# Create global LLM manager instance
llm_manager = LLMManager()

def get_llm_manager() -> LLMManager:
    """Get the global LLM manager instance."""
    return llm_manager
