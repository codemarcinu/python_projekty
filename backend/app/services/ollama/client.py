from typing import AsyncGenerator, Optional
import httpx
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout
        )

    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        stream: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Generate text using Ollama model.
        
        Args:
            prompt: Input prompt
            model: Optional model override
            stream: Whether to stream the response
            
        Yields:
            Generated text chunks
        """
        try:
            response = await self.client.post(
                "/api/generate",
                json={
                    "model": model or self.model,
                    "prompt": prompt,
                    "stream": stream
                }
            )
            response.raise_for_status()
            
            if stream:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk = response.json()
                            yield chunk.get("response", "")
                        except Exception as e:
                            logger.error(f"Error parsing stream chunk: {e}")
            else:
                data = response.json()
                yield data.get("response", "")
                
        except Exception as e:
            logger.error(f"Error generating with Ollama: {e}")
            raise

    async def list_models(self) -> list[str]:
        """List available Ollama models."""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose() 