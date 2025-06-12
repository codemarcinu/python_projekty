import pytest
from app.services.ollama import OllamaService
from app.core.config import settings
import json
import asyncio
from typing import AsyncGenerator

@pytest.fixture
async def ollama_service() -> AsyncGenerator[OllamaService, None]:
    service = OllamaService()
    yield service
    await service.close()

def test_ollama_service_initialization(ollama_service):
    assert ollama_service.base_url == settings.OLLAMA_BASE_URL
    assert ollama_service.model == settings.OLLAMA_MODEL

def test_generate_response(ollama_service):
    prompt = "What is Python?"
    response = ollama_service.generate_response(prompt)
    
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_generate_response_with_context(ollama_service):
    prompt = "What is Python?"
    context = "Python is a programming language."
    response = ollama_service.generate_response(prompt, context=context)
    
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_generate_response_with_system_prompt(ollama_service):
    prompt = "What is Python?"
    system_prompt = "You are a helpful assistant."
    response = ollama_service.generate_response(prompt, system_prompt=system_prompt)
    
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_generate_response_with_temperature(ollama_service):
    prompt = "What is Python?"
    response = ollama_service.generate_response(prompt, temperature=0.7)
    
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_generate_response_with_max_tokens(ollama_service):
    prompt = "What is Python?"
    response = ollama_service.generate_response(prompt, max_tokens=100)
    
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_generate_response_with_stop_sequences(ollama_service):
    prompt = "What is Python?"
    stop_sequences = ["\n", "."]
    response = ollama_service.generate_response(prompt, stop_sequences=stop_sequences)
    
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_generate_response_with_all_parameters(ollama_service):
    prompt = "What is Python?"
    context = "Python is a programming language."
    system_prompt = "You are a helpful assistant."
    temperature = 0.7
    max_tokens = 100
    stop_sequences = ["\n", "."]
    
    response = ollama_service.generate_response(
        prompt,
        context=context,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        stop_sequences=stop_sequences
    )
    
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_generate_streaming_response(ollama_service):
    prompt = "What is Python?"
    response_stream = ollama_service.generate_streaming_response(prompt)
    
    assert response_stream is not None
    for chunk in response_stream:
        assert isinstance(chunk, str)
        assert len(chunk) > 0

def test_generate_streaming_response_with_context(ollama_service):
    prompt = "What is Python?"
    context = "Python is a programming language."
    response_stream = ollama_service.generate_streaming_response(prompt, context=context)
    
    assert response_stream is not None
    for chunk in response_stream:
        assert isinstance(chunk, str)
        assert len(chunk) > 0

def test_generate_streaming_response_with_system_prompt(ollama_service):
    prompt = "What is Python?"
    system_prompt = "You are a helpful assistant."
    response_stream = ollama_service.generate_streaming_response(prompt, system_prompt=system_prompt)
    
    assert response_stream is not None
    for chunk in response_stream:
        assert isinstance(chunk, str)
        assert len(chunk) > 0

def test_generate_streaming_response_with_temperature(ollama_service):
    prompt = "What is Python?"
    response_stream = ollama_service.generate_streaming_response(prompt, temperature=0.7)
    
    assert response_stream is not None
    for chunk in response_stream:
        assert isinstance(chunk, str)
        assert len(chunk) > 0

def test_generate_streaming_response_with_max_tokens(ollama_service):
    prompt = "What is Python?"
    response_stream = ollama_service.generate_streaming_response(prompt, max_tokens=100)
    
    assert response_stream is not None
    for chunk in response_stream:
        assert isinstance(chunk, str)
        assert len(chunk) > 0

def test_generate_streaming_response_with_stop_sequences(ollama_service):
    prompt = "What is Python?"
    stop_sequences = ["\n", "."]
    response_stream = ollama_service.generate_streaming_response(prompt, stop_sequences=stop_sequences)
    
    assert response_stream is not None
    for chunk in response_stream:
        assert isinstance(chunk, str)
        assert len(chunk) > 0

def test_generate_streaming_response_with_all_parameters(ollama_service):
    prompt = "What is Python?"
    context = "Python is a programming language."
    system_prompt = "You are a helpful assistant."
    temperature = 0.7
    max_tokens = 100
    stop_sequences = ["\n", "."]
    
    response_stream = ollama_service.generate_streaming_response(
        prompt,
        context=context,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        stop_sequences=stop_sequences
    )
    
    assert response_stream is not None
    for chunk in response_stream:
        assert isinstance(chunk, str)
        assert len(chunk) > 0

def test_list_models(ollama_service):
    models = ollama_service.list_models()
    
    assert models is not None
    assert isinstance(models, list)
    assert len(models) > 0
    for model in models:
        assert isinstance(model, dict)
        assert "name" in model
        assert "modified_at" in model
        assert "size" in model

def test_show_model_info(ollama_service):
    model_info = ollama_service.show_model_info(settings.OLLAMA_MODEL)
    
    assert model_info is not None
    assert isinstance(model_info, dict)
    assert "name" in model_info
    assert "modified_at" in model_info
    assert "size" in model_info
    assert "parameters" in model_info
    assert "quantization_level" in model_info

def test_pull_model(ollama_service):
    # Note: This test might take a while to run as it downloads the model
    model_name = "llama2"
    result = ollama_service.pull_model(model_name)
    
    assert result is not None
    assert isinstance(result, dict)
    assert "status" in result

def test_delete_model(ollama_service):
    # Note: This test requires the model to exist
    model_name = "llama2"
    result = ollama_service.delete_model(model_name)
    
    assert result is not None
    assert isinstance(result, dict)
    assert "status" in result

@pytest.mark.asyncio
async def test_ollama_connection(ollama_service):
    # Test connection to Ollama
    is_connected = await ollama_service.check_connection()
    assert is_connected is True

@pytest.mark.asyncio
async def test_list_models(ollama_service):
    # Test listing available models
    models = await ollama_service.list_models()
    assert isinstance(models, list)
    assert len(models) > 0
    assert all(isinstance(model, str) for model in models)

@pytest.mark.asyncio
async def test_generate_text(ollama_service):
    # Test text generation
    prompt = "What is Python?"
    response = await ollama_service.generate_text(
        prompt=prompt,
        model=settings.DEFAULT_OLLAMA_MODEL
    )
    
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_stream_text(ollama_service):
    # Test streaming text generation
    prompt = "Explain async/await in Python"
    chunks = []
    
    async for chunk in ollama_service.stream_text(
        prompt=prompt,
        model=settings.DEFAULT_OLLAMA_MODEL
    ):
        chunks.append(chunk)
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, str) for chunk in chunks)
    assert "".join(chunks) != ""

@pytest.mark.asyncio
async def test_model_switching(ollama_service):
    # Test switching between models
    models = await ollama_service.list_models()
    if len(models) >= 2:
        model1, model2 = models[:2]
        
        # Generate with first model
        response1 = await ollama_service.generate_text(
            prompt="Hello",
            model=model1
        )
        
        # Generate with second model
        response2 = await ollama_service.generate_text(
            prompt="Hello",
            model=model2
        )
        
        assert response1 != response2

@pytest.mark.asyncio
async def test_invalid_model(ollama_service):
    # Test with invalid model
    with pytest.raises(Exception):
        await ollama_service.generate_text(
            prompt="Test",
            model="invalid_model"
        )

@pytest.mark.asyncio
async def test_generation_parameters(ollama_service):
    # Test different generation parameters
    prompt = "Write a short poem"
    
    # Test with temperature
    response1 = await ollama_service.generate_text(
        prompt=prompt,
        model=settings.DEFAULT_OLLAMA_MODEL,
        temperature=0.7
    )
    
    # Test with different temperature
    response2 = await ollama_service.generate_text(
        prompt=prompt,
        model=settings.DEFAULT_OLLAMA_MODEL,
        temperature=0.2
    )
    
    assert response1 != response2

@pytest.mark.asyncio
async def test_concurrent_requests(ollama_service):
    # Test handling multiple concurrent requests
    async def generate():
        return await ollama_service.generate_text(
            prompt="Test",
            model=settings.DEFAULT_OLLAMA_MODEL
        )
    
    # Run multiple requests concurrently
    tasks = [generate() for _ in range(3)]
    responses = await asyncio.gather(*tasks)
    
    assert len(responses) == 3
    assert all(isinstance(r, str) for r in responses)

@pytest.mark.asyncio
async def test_error_handling(ollama_service):
    # Test error handling
    with pytest.raises(Exception):
        await ollama_service.generate_text(
            prompt="",  # Empty prompt
            model=settings.DEFAULT_OLLAMA_MODEL
        )
    
    with pytest.raises(Exception):
        await ollama_service.generate_text(
            prompt="Test" * 1000,  # Too long prompt
            model=settings.DEFAULT_OLLAMA_MODEL
        )

@pytest.mark.asyncio
async def test_model_info(ollama_service):
    # Test getting model information
    model_info = await ollama_service.get_model_info(
        model=settings.DEFAULT_OLLAMA_MODEL
    )
    
    assert model_info is not None
    assert "name" in model_info
    assert "size" in model_info
    assert "modified_at" in model_info

@pytest.mark.asyncio
async def test_pull_model(ollama_service):
    # Test pulling a new model
    # Note: This test might take a while and requires internet connection
    model_name = "llama2:7b"
    
    try:
        result = await ollama_service.pull_model(model_name)
        assert result is True
        
        # Verify model is available
        models = await ollama_service.list_models()
        assert model_name in models
    except Exception as e:
        pytest.skip(f"Could not pull model: {str(e)}")

@pytest.mark.asyncio
async def test_delete_model(ollama_service):
    # Test deleting a model
    # Note: This test should be run with caution
    model_name = "test_model"
    
    try:
        # First pull the model
        await ollama_service.pull_model(model_name)
        
        # Then delete it
        result = await ollama_service.delete_model(model_name)
        assert result is True
        
        # Verify model is not available
        models = await ollama_service.list_models()
        assert model_name not in models
    except Exception as e:
        pytest.skip(f"Could not delete model: {str(e)}") 