import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from typing import Dict, Any

from app.services.ollama.service import OllamaService, OllamaConfig
from app.services.ollama.exceptions import (
    OllamaServiceError, OllamaConnectionError, ModelNotFoundError,
    ModelLoadError, GenerationError, EmbeddingError, ResourceLimitError,
    ContextError
)
from app.services.ollama.interfaces import ModelType
from app.core.config import settings

@pytest.fixture
def mock_config():
    """Create a mock Ollama configuration."""
    return OllamaConfig(
        base_url="http://localhost:11434",
        timeout=5,
        max_retries=2,
        retry_delay=0.1
    )

@pytest.fixture
def mock_session():
    """Create a mock aiohttp session."""
    return AsyncMock(spec=aiohttp.ClientSession)

@pytest.fixture
def ollama_service(mock_config, mock_session):
    """Create an OllamaService instance with mocked dependencies."""
    with patch("aiohttp.ClientSession", return_value=mock_session):
        service = OllamaService(config=mock_config)
        service.session = mock_session
        yield service

@pytest.fixture
def ollama_service():
    """Create an Ollama service instance."""
    return OllamaService(
        base_url=settings.OLLAMA_BASE_URL,
        timeout=settings.OLLAMA_TIMEOUT
    )

@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = Mock()
    response.status_code = 200
    response.json.return_value = {
        "model": "test-model",
        "response": "Test response",
        "done": True
    }
    return response

@pytest.mark.asyncio
async def test_list_models_success(ollama_service, mock_session):
    """Test successful model listing."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "models": [
            {
                "name": "deepseek-coder-v2:latest",
                "modified_at": "2024-03-20T12:00:00Z",
                "description": "Code generation model",
                "parameters": {"size": "7B"}
            }
        ]
    })
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    models = await ollama_service.list_models()
    
    assert len(models) == 1
    assert models[0].name == "deepseek-coder-v2:latest"
    assert models[0].type == ModelType.CODE
    assert models[0].description == "Code generation model"
    assert models[0].parameters == {"size": "7B"}

@pytest.mark.asyncio
async def test_list_models_error(ollama_service, mock_session):
    """Test error handling in model listing."""
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    with pytest.raises(ModelNotFoundError):
        await ollama_service.list_models()

@pytest.mark.asyncio
async def test_generate_success(ollama_service, mock_session):
    """Test successful text generation."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "response": "Generated text"
    })
    mock_session.post.return_value.__aenter__.return_value = mock_response
    
    result = await ollama_service.generate(
        prompt="Test prompt",
        model_name="mistral:latest"
    )
    
    assert result == "Generated text"
    mock_session.post.assert_called_once()

@pytest.mark.asyncio
async def test_generate_stream_success(ollama_service, mock_session):
    """Test successful streaming text generation."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.content = AsyncMock()
    mock_response.content.__aiter__.return_value = [
        json.dumps({"response": "chunk1"}).encode(),
        json.dumps({"response": "chunk2"}).encode()
    ]
    mock_session.post.return_value.__aenter__.return_value = mock_response
    
    chunks = []
    async for chunk in ollama_service.generate(
        prompt="Test prompt",
        model_name="mistral:latest",
        stream=True
    ):
        chunks.append(chunk)
    
    assert chunks == ["chunk1", "chunk2"]

@pytest.mark.asyncio
async def test_generate_with_context(ollama_service, mock_session):
    """Test text generation with context."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "response": "Generated with context"
    })
    mock_session.post.return_value.__aenter__.return_value = mock_response
    
    context = [
        {"role": "user", "content": "Previous message"},
        {"role": "assistant", "content": "Previous response"}
    ]
    
    result = await ollama_service.generate_with_context(
        prompt="New prompt",
        model_name="mistral:latest",
        context=context
    )
    
    assert result == "Generated with context"
    # Verify context was properly formatted in the request
    call_args = mock_session.post.call_args[1]["json"]
    assert "Previous message" in call_args["prompt"]
    assert "Previous response" in call_args["prompt"]

@pytest.mark.asyncio
async def test_get_embeddings_success(ollama_service, mock_session):
    """Test successful embedding generation."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={
        "embedding": [0.1, 0.2, 0.3]
    })
    mock_session.post.return_value.__aenter__.return_value = mock_response
    
    embeddings = await ollama_service.get_embeddings(
        text="Test text",
        model_name="nomic-embed-text:latest"
    )
    
    assert embeddings == [0.1, 0.2, 0.3]

@pytest.mark.asyncio
async def test_get_model_info_cached(ollama_service):
    """Test getting model info from cache."""
    model_info = {
        "name": "mistral:latest",
        "type": ModelType.CHAT,
        "description": "Test model",
        "parameters": {},
        "last_used": datetime.now()
    }
    ollama_service._model_cache["mistral:latest"] = model_info
    
    result = await ollama_service.get_model_info("mistral:latest")
    assert result == model_info

@pytest.mark.asyncio
async def test_get_model_info_not_found(ollama_service, mock_session):
    """Test getting info for non-existent model."""
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value={"models": []})
    mock_session.get.return_value.__aenter__.return_value = mock_response
    
    result = await ollama_service.get_model_info("non-existent-model")
    assert result is None

@pytest.mark.asyncio
async def test_performance_metrics(ollama_service):
    """Test performance metrics tracking."""
    model_name = "mistral:latest"
    start_time = datetime.now()
    end_time = datetime.now()
    tokens = 100
    
    await ollama_service._update_performance_metrics(
        model_name, start_time, end_time, tokens
    )
    
    metrics = await ollama_service.get_performance_metrics(model_name)
    assert "last_duration" in metrics
    assert "last_tokens_per_second" in metrics
    assert "total_tokens" in metrics
    assert "total_duration" in metrics

@pytest.mark.asyncio
async def test_resource_limits(ollama_service):
    """Test resource limit checking."""
    with patch("psutil.cpu_percent", return_value=95.0), \
         patch("psutil.virtual_memory") as mock_memory:
        mock_memory.return_value.percent = 50.0
        
        with pytest.raises(ResourceLimitError):
            await ollama_service._check_resources()

@pytest.mark.asyncio
async def test_connection_error(ollama_service, mock_session):
    """Test connection error handling."""
    mock_session.get.side_effect = aiohttp.ClientError
    
    with pytest.raises(OllamaConnectionError):
        await ollama_service._check_connection()

@pytest.mark.asyncio
async def test_context_formatting(ollama_service):
    """Test conversation context formatting."""
    context = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
        {"role": "user", "content": "How are you?"}
    ]
    
    formatted = ollama_service._format_context(context)
    assert "User: Hello" in formatted
    assert "Assistant: Hi there" in formatted
    assert "User: How are you?" in formatted

@pytest.mark.asyncio
async def test_model_type_determination(ollama_service):
    """Test model type determination based on name."""
    assert ollama_service._determine_model_type("deepseek-coder-v2:latest") == ModelType.CODE
    assert ollama_service._determine_model_type("nomic-embed-text:latest") == ModelType.EMBEDDING
    assert ollama_service._determine_model_type("mistral:latest") == ModelType.CHAT

@pytest.mark.asyncio
async def test_list_models(ollama_service, mock_response):
    """Test listing available models."""
    with patch('aiohttp.ClientSession.get', return_value=AsyncMock(return_value=mock_response)):
        models = await ollama_service.list_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert all(isinstance(model, dict) for model in models)

@pytest.mark.asyncio
async def test_generate_text(ollama_service, mock_response):
    """Test text generation."""
    with patch('aiohttp.ClientSession.post', return_value=AsyncMock(return_value=mock_response)):
        response = await ollama_service.generate_text(
            prompt="Test prompt",
            model="test-model",
            context=["Previous message"]
        )
        assert response == "Test response"

@pytest.mark.asyncio
async def test_generate_stream(ollama_service):
    """Test streaming text generation."""
    mock_stream = AsyncMock()
    mock_stream.__aiter__.return_value = [
        {"response": "Part 1", "done": False},
        {"response": "Part 2", "done": False},
        {"response": "Part 3", "done": True}
    ]
    
    with patch('aiohttp.ClientSession.post', return_value=AsyncMock(return_value=mock_stream)):
        responses = []
        async for response in ollama_service.generate_stream(
            prompt="Test prompt",
            model="test-model"
        ):
            responses.append(response)
        
        assert len(responses) == 3
        assert responses == ["Part 1", "Part 2", "Part 3"]

@pytest.mark.asyncio
async def test_get_embeddings(ollama_service, mock_response):
    """Test getting embeddings."""
    mock_response.json.return_value = {
        "embedding": [0.1, 0.2, 0.3]
    }
    
    with patch('aiohttp.ClientSession.post', return_value=AsyncMock(return_value=mock_response)):
        embedding = await ollama_service.get_embeddings(
            text="Test text",
            model="test-model"
        )
        assert isinstance(embedding, list)
        assert len(embedding) == 3
        assert all(isinstance(x, float) for x in embedding)

@pytest.mark.asyncio
async def test_connection_error(ollama_service):
    """Test connection error handling."""
    with patch('aiohttp.ClientSession.get', side_effect=Exception("Connection error")):
        with pytest.raises(OllamaConnectionError):
            await ollama_service.list_models()

@pytest.mark.asyncio
async def test_model_not_found(ollama_service):
    """Test model not found error handling."""
    mock_response = Mock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"error": "Model not found"}
    
    with patch('aiohttp.ClientSession.post', return_value=AsyncMock(return_value=mock_response)):
        with pytest.raises(ModelNotFoundError):
            await ollama_service.generate_text(
                prompt="Test prompt",
                model="nonexistent-model"
            )

@pytest.mark.asyncio
async def test_resource_limit(ollama_service):
    """Test resource limit error handling."""
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.json.return_value = {"error": "Resource limit exceeded"}
    
    with patch('aiohttp.ClientSession.post', return_value=AsyncMock(return_value=mock_response)):
        with pytest.raises(ResourceLimitError):
            await ollama_service.generate_text(
                prompt="Test prompt",
                model="test-model"
            )

@pytest.mark.asyncio
async def test_context_error(ollama_service):
    """Test context error handling."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "Context too large"}
    
    with patch('aiohttp.ClientSession.post', return_value=AsyncMock(return_value=mock_response)):
        with pytest.raises(ContextError):
            await ollama_service.generate_text(
                prompt="Test prompt",
                model="test-model",
                context=["x" * 1000000]  # Very large context
            )

@pytest.mark.asyncio
async def test_model_info(ollama_service, mock_response):
    """Test getting model information."""
    mock_response.json.return_value = {
        "name": "test-model",
        "parameters": 7,
        "quantization_level": "4-bit",
        "context_length": 2048
    }
    
    with patch('aiohttp.ClientSession.get', return_value=AsyncMock(return_value=mock_response)):
        info = await ollama_service.get_model_info("test-model")
        assert info["name"] == "test-model"
        assert info["parameters"] == 7
        assert info["quantization_level"] == "4-bit"
        assert info["context_length"] == 2048

@pytest.mark.asyncio
async def test_performance_metrics(ollama_service):
    """Test performance metrics tracking."""
    # Generate some responses
    with patch('aiohttp.ClientSession.post', return_value=AsyncMock(return_value=mock_response)):
        await ollama_service.generate_text(
            prompt="Test prompt 1",
            model="test-model"
        )
        await ollama_service.generate_text(
            prompt="Test prompt 2",
            model="test-model"
        )
    
    # Get metrics
    metrics = ollama_service.get_performance_metrics("test-model")
    assert metrics["total_requests"] == 2
    assert metrics["successful_requests"] == 2
    assert metrics["failed_requests"] == 0
    assert "average_response_time" in metrics
    assert "last_used" in metrics

@pytest.mark.asyncio
async def test_cleanup(ollama_service):
    """Test cleanup of old metrics."""
    # Add some old metrics
    ollama_service._performance_metrics["old-model"] = {
        "last_used": datetime.now().timestamp() - 86400,  # 24 hours ago
        "total_requests": 10
    }
    
    # Cleanup
    ollama_service.cleanup_old_metrics(max_age_hours=12)
    
    # Check if old metrics were removed
    assert "old-model" not in ollama_service._performance_metrics 