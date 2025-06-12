import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

from app.main import app
from app.services.ollama.service import OllamaService
from app.services.ollama.exceptions import OllamaServiceError
from app.core.config import settings

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

@pytest.fixture
def mock_ollama_service():
    """Create a mock Ollama service."""
    with patch("app.api.deps.get_ollama_service") as mock:
        service = AsyncMock(spec=OllamaService)
        mock.return_value = service
        yield service

def test_chat_endpoint_success(client, mock_ollama_service):
    """Test successful chat endpoint."""
    # Mock response
    mock_ollama_service.generate.return_value = "Generated response"
    mock_ollama_service.get_performance_metrics.return_value = {
        "total_tokens": 100,
        "last_duration": 1.5
    }
    
    # Make request
    response = client.post(
        "/api/v1/chat/chat",
        json={
            "message": "Test message",
            "model_name": "mistral:latest"
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "Generated response"
    assert data["model_name"] == "mistral:latest"
    assert data["tokens_generated"] == 100
    assert data["duration"] == 1.5
    
    # Verify service call
    mock_ollama_service.generate.assert_called_once_with(
        prompt="Test message",
        model_name="mistral:latest",
        stream=False,
        temperature=None,
        max_tokens=None
    )

def test_chat_endpoint_error(client, mock_ollama_service):
    """Test chat endpoint error handling."""
    # Mock error
    mock_ollama_service.generate.side_effect = OllamaServiceError("Test error")
    
    # Make request
    response = client.post(
        "/api/v1/chat/chat",
        json={
            "message": "Test message",
            "model_name": "mistral:latest"
        }
    )
    
    # Check response
    assert response.status_code == 500
    assert response.json()["detail"] == "Test error"

def test_list_models_success(client, mock_ollama_service):
    """Test successful model listing."""
    # Mock response
    mock_ollama_service.list_models.return_value = [
        {
            "name": "mistral:latest",
            "type": "chat",
            "description": "Test model",
            "parameters": {"size": "7B"}
        }
    ]
    
    # Make request
    response = client.get("/api/v1/chat/models")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "mistral:latest"
    assert data[0]["type"] == "chat"
    assert data[0]["description"] == "Test model"
    assert data[0]["parameters"] == {"size": "7B"}

def test_get_model_info_success(client, mock_ollama_service):
    """Test successful model info retrieval."""
    # Mock response
    mock_ollama_service.get_model_info.return_value = {
        "name": "mistral:latest",
        "type": "chat",
        "description": "Test model",
        "parameters": {"size": "7B"}
    }
    
    # Make request
    response = client.get("/api/v1/chat/models/mistral:latest")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "mistral:latest"
    assert data["type"] == "chat"
    assert data["description"] == "Test model"
    assert data["parameters"] == {"size": "7B"}

def test_get_model_info_not_found(client, mock_ollama_service):
    """Test model info retrieval for non-existent model."""
    # Mock response
    mock_ollama_service.get_model_info.return_value = None
    
    # Make request
    response = client.get("/api/v1/chat/models/non-existent-model")
    
    # Check response
    assert response.status_code == 404
    assert response.json()["detail"] == "Model non-existent-model not found"

@pytest.mark.asyncio
async def test_websocket_chat_success():
    """Test successful WebSocket chat."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    with client.websocket_connect("/api/v1/chat/ws") as websocket:
        # Mock Ollama service
        with patch("app.api.deps.get_ollama_service") as mock:
            service = AsyncMock(spec=OllamaService)
            service.generate.return_value = ["chunk1", "chunk2"]
            mock.return_value = service
            
            # Send message
            websocket.send_text(json.dumps({
                "message": "Test message",
                "model_name": "mistral:latest"
            }))
            
            # Receive chunks
            chunk1 = json.loads(websocket.receive_text())
            assert chunk1["type"] == "chunk"
            assert chunk1["content"] == "chunk1"
            
            chunk2 = json.loads(websocket.receive_text())
            assert chunk2["type"] == "chunk"
            assert chunk2["content"] == "chunk2"
            
            # Receive completion
            complete = json.loads(websocket.receive_text())
            assert complete["type"] == "complete"

@pytest.mark.asyncio
async def test_websocket_chat_error():
    """Test WebSocket chat error handling."""
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    with client.websocket_connect("/api/v1/chat/ws") as websocket:
        # Mock Ollama service error
        with patch("app.api.deps.get_ollama_service") as mock:
            service = AsyncMock(spec=OllamaService)
            service.generate.side_effect = OllamaServiceError("Test error")
            mock.return_value = service
            
            # Send message
            websocket.send_text(json.dumps({
                "message": "Test message",
                "model_name": "mistral:latest"
            }))
            
            # Receive error
            error = json.loads(websocket.receive_text())
            assert error["type"] == "error"
            assert error["message"] == "Test error" 