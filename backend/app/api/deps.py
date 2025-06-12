from typing import Generator, Optional
from fastapi import Depends

from app.services.ollama.service import OllamaService, OllamaConfig
from app.core.config import settings

async def get_ollama_service() -> Generator[OllamaService, None, None]:
    """Get Ollama service instance."""
    config = OllamaConfig(
        base_url=settings.OLLAMA_BASE_URL,
        timeout=settings.OLLAMA_TIMEOUT,
        max_retries=settings.OLLAMA_MAX_RETRIES,
        retry_delay=settings.OLLAMA_RETRY_DELAY,
        max_context_length=settings.OLLAMA_MAX_CONTEXT_LENGTH,
        max_tokens=settings.OLLAMA_MAX_TOKENS,
        temperature=settings.OLLAMA_TEMPERATURE,
        top_p=settings.OLLAMA_TOP_P,
        top_k=settings.OLLAMA_TOP_K,
        repeat_penalty=settings.OLLAMA_REPEAT_PENALTY,
        stop_sequences=settings.OLLAMA_STOP_SEQUENCES,
        resource_limits=settings.OLLAMA_RESOURCE_LIMITS
    )
    
    service = OllamaService(config=config)
    try:
        async with service:
            yield service
    finally:
        # Cleanup will be handled by the context manager
        pass 