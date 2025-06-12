import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import json

from app.main import app
from app.core.security import create_access_token
from app.core.config import settings

client = TestClient(app)

@pytest.fixture
def test_user():
    """Create a test user."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User"
    }

@pytest.fixture
def test_token(test_user):
    """Create a test token."""
    return create_access_token({"sub": test_user["username"]})

@pytest.fixture
def auth_headers(test_token):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {test_token}"}

def test_chat_endpoint_unauthorized():
    """Test chat endpoint without authorization."""
    response = client.post("/api/v1/chat", json={
        "message": "Hello",
        "model": "test-model"
    })
    assert response.status_code == 401

def test_chat_endpoint_success(auth_headers):
    """Test successful chat request."""
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
            "model": "test-model",
            "temperature": 0.7,
            "max_tokens": 100
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "message" in data
    assert "model" in data
    assert "usage" in data

def test_chat_endpoint_invalid_request(auth_headers):
    """Test chat endpoint with invalid request."""
    response = client.post(
        "/api/v1/chat",
        json={
            "message": "",  # Empty message
            "model": "test-model"
        },
        headers=auth_headers
    )
    assert response.status_code == 422

def test_chat_endpoint_rate_limit(auth_headers):
    """Test chat endpoint rate limiting."""
    # Make multiple requests quickly
    for _ in range(11):  # Exceed the 10/minute limit
        response = client.post(
            "/api/v1/chat",
            json={
                "message": "Hello",
                "model": "test-model"
            },
            headers=auth_headers
        )
    
    # Last request should be rate limited
    assert response.status_code == 429
    assert "retry_after" in response.json()

def test_websocket_chat(auth_headers):
    """Test WebSocket chat endpoint."""
    with client.websocket_connect(
        "/api/v1/ws/chat",
        headers=auth_headers
    ) as websocket:
        # Send message
        websocket.send_json({
            "message": "Hello",
            "model": "test-model"
        })
        
        # Receive response
        response = websocket.receive_json()
        assert "conversation_id" in response
        assert "content" in response
        assert "model" in response

def test_list_conversations(auth_headers):
    """Test listing conversations."""
    response = client.get("/api/v1/conversations", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_get_conversation(auth_headers):
    """Test getting a specific conversation."""
    # First create a conversation
    chat_response = client.post(
        "/api/v1/chat",
        json={
            "message": "Hello",
            "model": "test-model"
        },
        headers=auth_headers
    )
    conversation_id = chat_response.json()["conversation_id"]
    
    # Then get it
    response = client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conversation_id
    assert len(data["messages"]) > 0

def test_create_conversation(auth_headers):
    """Test creating a new conversation."""
    response = client.post(
        "/api/v1/conversations",
        json={
            "title": "Test Conversation",
            "initial_message": "Hello",
            "metadata": {"source": "test"}
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Conversation"
    assert len(data["messages"]) == 1
    assert data["metadata"]["source"] == "test"

def test_update_conversation(auth_headers):
    """Test updating a conversation."""
    # First create a conversation
    create_response = client.post(
        "/api/v1/conversations",
        json={
            "title": "Original Title",
            "initial_message": "Hello"
        },
        headers=auth_headers
    )
    conversation_id = create_response.json()["id"]
    
    # Then update it
    response = client.put(
        f"/api/v1/conversations/{conversation_id}",
        json={
            "title": "Updated Title",
            "metadata": {"updated": True}
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["metadata"]["updated"] is True

def test_delete_conversation(auth_headers):
    """Test deleting a conversation."""
    # First create a conversation
    create_response = client.post(
        "/api/v1/conversations",
        json={
            "title": "Test Conversation",
            "initial_message": "Hello"
        },
        headers=auth_headers
    )
    conversation_id = create_response.json()["id"]
    
    # Then delete it
    response = client.delete(
        f"/api/v1/conversations/{conversation_id}",
        headers=auth_headers
    )
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404

def test_invalid_token():
    """Test with invalid token."""
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello"},
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

def test_expired_token():
    """Test with expired token."""
    # Create an expired token
    expired_token = create_access_token(
        {"sub": "testuser"},
        expires_delta=timedelta(microseconds=1)
    )
    
    # Wait for token to expire
    import time
    time.sleep(0.1)
    
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello"},
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401 