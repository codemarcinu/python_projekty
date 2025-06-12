import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.user import UserService
from app.services.chat import ChatService
from app.services.message import MessageService
from app.services.document import DocumentService
from app.services.tag import TagService
import uuid

client = TestClient(app)

@pytest.fixture
def user_service(db_session):
    return UserService(db_session)

@pytest.fixture
def chat_service(db_session):
    return ChatService(db_session)

@pytest.fixture
def message_service(db_session):
    return MessageService(db_session)

@pytest.fixture
def document_service(db_session):
    return DocumentService(db_session)

@pytest.fixture
def tag_service(db_session):
    return TagService(db_session)

def test_create_user():
    response = client.post(
        "/api/v1/users/",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test User"
    assert data["email"] == "test@example.com"

def test_get_user(user_service):
    # Create user first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    
    response = client.get(f"/api/v1/users/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["name"] == "Test User"
    assert data["email"] == "test@example.com"

def test_update_user(user_service):
    # Create user first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    
    response = client.put(
        f"/api/v1/users/{user.id}",
        json={
            "name": "Updated User",
            "email": "updated@example.com"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated User"
    assert data["email"] == "updated@example.com"

def test_delete_user(user_service):
    # Create user first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    
    response = client.delete(f"/api/v1/users/{user.id}")
    assert response.status_code == 200
    
    # Verify user is deleted
    response = client.get(f"/api/v1/users/{user.id}")
    assert response.status_code == 404

def test_create_chat(user_service):
    # Create user first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    
    response = client.post(
        "/api/v1/chats/",
        json={
            "user_id": user.id,
            "title": "Test Chat",
            "chat": {"messages": []}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Chat"
    assert data["user_id"] == user.id

def test_get_chat(chat_service, user_service):
    # Create user and chat first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    chat = chat_service.create_chat(
        user_id=user.id,
        title="Test Chat",
        chat={"messages": []}
    )
    
    response = client.get(f"/api/v1/chats/{chat.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == chat.id
    assert data["title"] == "Test Chat"
    assert data["user_id"] == user.id

def test_update_chat(chat_service, user_service):
    # Create user and chat first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    chat = chat_service.create_chat(
        user_id=user.id,
        title="Test Chat",
        chat={"messages": []}
    )
    
    response = client.put(
        f"/api/v1/chats/{chat.id}",
        json={
            "title": "Updated Chat",
            "chat": {"messages": [{"role": "user", "content": "Hello"}]}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Chat"
    assert data["chat"] == {"messages": [{"role": "user", "content": "Hello"}]}

def test_delete_chat(chat_service, user_service):
    # Create user and chat first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    chat = chat_service.create_chat(
        user_id=user.id,
        title="Test Chat",
        chat={"messages": []}
    )
    
    response = client.delete(f"/api/v1/chats/{chat.id}")
    assert response.status_code == 200
    
    # Verify chat is deleted
    response = client.get(f"/api/v1/chats/{chat.id}")
    assert response.status_code == 404

def test_create_message(message_service, chat_service, user_service):
    # Create user and chat first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    chat = chat_service.create_chat(
        user_id=user.id,
        title="Test Chat",
        chat={"messages": []}
    )
    
    response = client.post(
        "/api/v1/messages/",
        json={
            "chat_id": chat.id,
            "user_id": user.id,
            "content": "Test message",
            "role": "user"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Test message"
    assert data["role"] == "user"
    assert data["chat_id"] == chat.id
    assert data["user_id"] == user.id

def test_get_message(message_service, chat_service, user_service):
    # Create user, chat and message first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    chat = chat_service.create_chat(
        user_id=user.id,
        title="Test Chat",
        chat={"messages": []}
    )
    message = message_service.create_message(
        chat_id=chat.id,
        user_id=user.id,
        content="Test message",
        role="user"
    )
    
    response = client.get(f"/api/v1/messages/{message.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == message.id
    assert data["content"] == "Test message"
    assert data["role"] == "user"

def test_update_message(message_service, chat_service, user_service):
    # Create user, chat and message first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    chat = chat_service.create_chat(
        user_id=user.id,
        title="Test Chat",
        chat={"messages": []}
    )
    message = message_service.create_message(
        chat_id=chat.id,
        user_id=user.id,
        content="Test message",
        role="user"
    )
    
    response = client.put(
        f"/api/v1/messages/{message.id}",
        json={
            "content": "Updated message",
            "role": "assistant"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Updated message"
    assert data["role"] == "assistant"

def test_delete_message(message_service, chat_service, user_service):
    # Create user, chat and message first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    chat = chat_service.create_chat(
        user_id=user.id,
        title="Test Chat",
        chat={"messages": []}
    )
    message = message_service.create_message(
        chat_id=chat.id,
        user_id=user.id,
        content="Test message",
        role="user"
    )
    
    response = client.delete(f"/api/v1/messages/{message.id}")
    assert response.status_code == 200
    
    # Verify message is deleted
    response = client.get(f"/api/v1/messages/{message.id}")
    assert response.status_code == 404

def test_create_document(document_service, user_service):
    # Create user first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    
    response = client.post(
        "/api/v1/documents/",
        json={
            "user_id": user.id,
            "collection_name": "test",
            "name": "test_doc",
            "title": "Test Document",
            "filename": "test.txt",
            "content": "Test content"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Document"
    assert data["content"] == "Test content"
    assert data["user_id"] == user.id

def test_get_document(document_service, user_service):
    # Create user and document first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    document = document_service.create_document(
        user_id=user.id,
        collection_name="test",
        name="test_doc",
        title="Test Document",
        filename="test.txt",
        content="Test content"
    )
    
    response = client.get(f"/api/v1/documents/{document.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == document.id
    assert data["title"] == "Test Document"
    assert data["content"] == "Test content"

def test_update_document(document_service, user_service):
    # Create user and document first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    document = document_service.create_document(
        user_id=user.id,
        collection_name="test",
        name="test_doc",
        title="Test Document",
        filename="test.txt",
        content="Test content"
    )
    
    response = client.put(
        f"/api/v1/documents/{document.id}",
        json={
            "title": "Updated Document",
            "content": "Updated content"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Document"
    assert data["content"] == "Updated content"

def test_delete_document(document_service, user_service):
    # Create user and document first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    document = document_service.create_document(
        user_id=user.id,
        collection_name="test",
        name="test_doc",
        title="Test Document",
        filename="test.txt",
        content="Test content"
    )
    
    response = client.delete(f"/api/v1/documents/{document.id}")
    assert response.status_code == 200
    
    # Verify document is deleted
    response = client.get(f"/api/v1/documents/{document.id}")
    assert response.status_code == 404

def test_create_tag(tag_service, user_service):
    # Create user first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    
    response = client.post(
        "/api/v1/tags/",
        json={
            "user_id": user.id,
            "name": "test_tag"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_tag"
    assert data["user_id"] == user.id

def test_get_tag(tag_service, user_service):
    # Create user and tag first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    tag = tag_service.create_tag(
        user_id=user.id,
        name="test_tag"
    )
    
    response = client.get(f"/api/v1/tags/{tag.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == tag.id
    assert data["name"] == "test_tag"
    assert data["user_id"] == user.id

def test_update_tag(tag_service, user_service):
    # Create user and tag first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    tag = tag_service.create_tag(
        user_id=user.id,
        name="test_tag"
    )
    
    response = client.put(
        f"/api/v1/tags/{tag.id}",
        json={
            "name": "updated_tag",
            "meta": {"color": "blue"}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated_tag"
    assert data["meta"] == {"color": "blue"}

def test_delete_tag(tag_service, user_service):
    # Create user and tag first
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    tag = tag_service.create_tag(
        user_id=user.id,
        name="test_tag"
    )
    
    response = client.delete(f"/api/v1/tags/{tag.id}")
    assert response.status_code == 200
    
    # Verify tag is deleted
    response = client.get(f"/api/v1/tags/{tag.id}")
    assert response.status_code == 404 