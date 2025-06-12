import logging
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import aiohttp
import psutil
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

from app.services.ollama.interfaces import OllamaServiceInterface, ModelInfo, ModelType
from app.services.ollama.exceptions import (
    OllamaServiceError, OllamaConnectionError, ModelNotFoundError,
    ModelLoadError, GenerationError, EmbeddingError, ResourceLimitError,
    ContextError
)

logger = logging.getLogger(__name__)

@dataclass
class OllamaConfig:
    """Configuration for Ollama service."""
    base_url: str = "http://localhost:11434"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    max_context_length: int = 4096
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1
    stop_sequences: List[str] = field(default_factory=list)
    resource_limits: Dict[str, float] = field(default_factory=lambda: {
        "cpu_percent": 90.0,
        "memory_percent": 90.0,
        "gpu_memory_percent": 90.0
    })

class OllamaService(OllamaServiceInterface):
    """Service for interacting with Ollama."""
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        """Initialize the Ollama service."""
        self.config = config or OllamaConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self._model_cache: Dict[str, ModelInfo] = {}
        self._performance_metrics: Dict[str, Dict[str, float]] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    async def __aenter__(self):
        """Set up async context."""
        if not self.session:
            self.session = aiohttp.ClientSession(
                base_url=self.config.base_url,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up async context."""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _check_connection(self) -> None:
        """Check connection to Ollama server."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    base_url=self.config.base_url,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                )
            
            async with self.session.get("/api/tags") as response:
                if response.status != 200:
                    raise OllamaConnectionError(
                        f"Ollama server returned status {response.status}"
                    )
        except Exception as e:
            raise OllamaConnectionError(f"Failed to connect to Ollama: {str(e)}")
    
    async def _check_resources(self) -> None:
        """Check if resource usage is within limits."""
        try:
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > self.config.resource_limits["cpu_percent"]:
                raise ResourceLimitError(f"CPU usage too high: {cpu_percent}%")
            
            if memory_percent > self.config.resource_limits["memory_percent"]:
                raise ResourceLimitError(f"Memory usage too high: {memory_percent}%")
            
            # TODO: Add GPU monitoring if available
            
        except Exception as e:
            raise ResourceLimitError(f"Resource check failed: {str(e)}")
    
    async def _update_performance_metrics(
        self,
        model_name: str,
        start_time: datetime,
        end_time: datetime,
        tokens_generated: int
    ) -> None:
        """Update performance metrics for a model."""
        if model_name not in self._performance_metrics:
            self._performance_metrics[model_name] = {}
        
        duration = (end_time - start_time).total_seconds()
        tokens_per_second = tokens_generated / duration if duration > 0 else 0
        
        self._performance_metrics[model_name].update({
            "last_duration": duration,
            "last_tokens_per_second": tokens_per_second,
            "total_tokens": self._performance_metrics[model_name].get("total_tokens", 0) + tokens_generated,
            "total_duration": self._performance_metrics[model_name].get("total_duration", 0) + duration
        })
    
    async def list_models(self) -> List[ModelInfo]:
        """List available Ollama models."""
        try:
            await self._check_connection()
            
            async with self.session.get("/api/tags") as response:
                if response.status != 200:
                    raise ModelNotFoundError(
                        f"Failed to list models: {response.status}"
                    )
                
                data = await response.json()
                models = []
                
                for model in data.get("models", []):
                    model_info = ModelInfo(
                        name=model["name"],
                        type=self._determine_model_type(model["name"]),
                        description=model.get("description", ""),
                        parameters=model.get("parameters", {}),
                        last_used=datetime.fromisoformat(model["modified_at"])
                        if "modified_at" in model else None
                    )
                    models.append(model_info)
                    self._model_cache[model["name"]] = model_info
                
                return models
                
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            raise ModelNotFoundError(f"Failed to list models: {str(e)}")
    
    def _determine_model_type(self, model_name: str) -> ModelType:
        """Determine the type of model based on its name."""
        model_name = model_name.lower()
        
        if "embed" in model_name:
            return ModelType.EMBEDDING
        elif any(code_model in model_name for code_model in ["code", "coder"]):
            return ModelType.CODE
        else:
            return ModelType.CHAT
    
    async def generate(
        self,
        prompt: str,
        model_name: str,
        stream: bool = False,
        **kwargs
    ) -> AsyncGenerator[str, None] | str:
        """Generate text using specified model."""
        try:
            await self._check_connection()
            await self._check_resources()
            
            # Prepare request data
            data = {
                "model": model_name,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": kwargs.get("temperature", self.config.temperature),
                    "top_p": kwargs.get("top_p", self.config.top_p),
                    "top_k": kwargs.get("top_k", self.config.top_k),
                    "repeat_penalty": kwargs.get("repeat_penalty", self.config.repeat_penalty),
                    "stop": kwargs.get("stop_sequences", self.config.stop_sequences),
                    "num_predict": kwargs.get("max_tokens", self.config.max_tokens)
                }
            }
            
            start_time = datetime.now()
            
            if stream:
                return self._stream_generation(data, model_name, start_time)
            else:
                return await self._generate_sync(data, model_name, start_time)
                
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise GenerationError(f"Failed to generate text: {str(e)}")
    
    async def _stream_generation(
        self,
        data: Dict[str, Any],
        model_name: str,
        start_time: datetime
    ) -> AsyncGenerator[str, None]:
        """Stream text generation."""
        try:
            async with self.session.post("/api/generate", json=data) as response:
                if response.status != 200:
                    raise GenerationError(f"Generation failed: {response.status}")
                
                tokens_generated = 0
                async for line in response.content:
                    if line:
                        try:
                            chunk = json.loads(line)
                            if "response" in chunk:
                                tokens_generated += 1
                                yield chunk["response"]
                        except json.JSONDecodeError:
                            continue
                
                end_time = datetime.now()
                await self._update_performance_metrics(
                    model_name, start_time, end_time, tokens_generated
                )
                
        except Exception as e:
            logger.error(f"Error in stream generation: {e}")
            raise GenerationError(f"Stream generation failed: {str(e)}")
    
    async def _generate_sync(
        self,
        data: Dict[str, Any],
        model_name: str,
        start_time: datetime
    ) -> str:
        """Generate text synchronously."""
        try:
            async with self.session.post("/api/generate", json=data) as response:
                if response.status != 200:
                    raise GenerationError(f"Generation failed: {response.status}")
                
                result = await response.json()
                end_time = datetime.now()
                
                # Estimate tokens (rough approximation)
                tokens_generated = len(result.get("response", "").split())
                
                await self._update_performance_metrics(
                    model_name, start_time, end_time, tokens_generated
                )
                
                return result.get("response", "")
                
        except Exception as e:
            logger.error(f"Error in sync generation: {e}")
            raise GenerationError(f"Sync generation failed: {str(e)}")
    
    async def generate_with_context(
        self,
        prompt: str,
        model_name: str,
        context: List[Dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> AsyncGenerator[str, None] | str:
        """Generate text with conversation context."""
        try:
            # Format context into prompt
            formatted_context = self._format_context(context)
            full_prompt = f"{formatted_context}\n\nUser: {prompt}\nAssistant:"
            
            return await self.generate(
                prompt=full_prompt,
                model_name=model_name,
                stream=stream,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"Error generating with context: {e}")
            raise ContextError(f"Failed to generate with context: {str(e)}")
    
    def _format_context(self, context: List[Dict[str, str]]) -> str:
        """Format conversation context into a prompt."""
        try:
            formatted_messages = []
            for msg in context:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                formatted_messages.append(f"{role.capitalize()}: {content}")
            
            return "\n".join(formatted_messages)
            
        except Exception as e:
            logger.error(f"Error formatting context: {e}")
            raise ContextError(f"Failed to format context: {str(e)}")
    
    async def get_embeddings(
        self,
        text: str,
        model_name: str = "nomic-embed-text:latest"
    ) -> List[float]:
        """Get embeddings for text."""
        try:
            await self._check_connection()
            
            data = {
                "model": model_name,
                "prompt": text
            }
            
            async with self.session.post("/api/embeddings", json=data) as response:
                if response.status != 200:
                    raise EmbeddingError(f"Embedding failed: {response.status}")
                
                result = await response.json()
                return result.get("embedding", [])
                
        except Exception as e:
            logger.error(f"Error getting embeddings: {e}")
            raise EmbeddingError(f"Failed to get embeddings: {str(e)}")
    
    async def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        try:
            # Check cache first
            if model_name in self._model_cache:
                return self._model_cache[model_name]
            
            # Get from server
            models = await self.list_models()
            for model in models:
                if model.name == model_name:
                    return model
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            raise ModelNotFoundError(f"Failed to get model info: {str(e)}")
    
    async def get_performance_metrics(self, model_name: str) -> Dict[str, float]:
        """Get performance metrics for a model."""
        try:
            if model_name not in self._performance_metrics:
                return {}
            
            metrics = self._performance_metrics[model_name]
            total_tokens = metrics.get("total_tokens", 0)
            total_duration = metrics.get("total_duration", 0)
            
            return {
                "last_duration": metrics.get("last_duration", 0),
                "last_tokens_per_second": metrics.get("last_tokens_per_second", 0),
                "total_tokens": total_tokens,
                "total_duration": total_duration,
                "average_tokens_per_second": total_tokens / total_duration
                if total_duration > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {} 