import pytest
from sqlalchemy.orm import Session
from app.services.user import UserService
from app.services.chat import ChatService
from app.services.message import MessageService
from app.services.document import DocumentService
from app.services.tag import TagService
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message
from app.models.document import Document
from app.models.tag import Tag
import uuid

@pytest.fixture
def user_service(db_session: Session):
    return UserService(db_session)

@pytest.fixture
def chat_service(db_session: Session):
    return ChatService(db_session)

@pytest.fixture
def message_service(db_session: Session):
    return MessageService(db_session)

@pytest.fixture
def document_service(db_session: Session):
    return DocumentService(db_session)

@pytest.fixture
def tag_service(db_session: Session):
    return TagService(db_session)

def test_user_service(user_service: UserService, db_session: Session):
    # Create user
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    
    # Get user
    retrieved_user = user_service.get_user(user.id)
    assert retrieved_user.id == user.id
    assert retrieved_user.name == user.name
    assert retrieved_user.email == user.email
    
    # Update user
    updated_user = user_service.update_user(
        user.id,
        name="Updated User",
        email="updated@example.com"
    )
    assert updated_user.name == "Updated User"
    assert updated_user.email == "updated@example.com"
    
    # Delete user
    user_service.delete_user(user.id)
    assert user_service.get_user(user.id) is None

def test_chat_service(chat_service: ChatService, user_service: UserService, db_session: Session):
    # Create user
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    
    # Create chat
    chat = chat_service.create_chat(
        user_id=user.id,
        title="Test Chat",
        chat={"messages": []}
    )
    assert chat.title == "Test Chat"
    assert chat.user_id == user.id
    
    # Get chat
    retrieved_chat = chat_service.get_chat(chat.id)
    assert retrieved_chat.id == chat.id
    assert retrieved_chat.title == chat.title
    
    # Update chat
    updated_chat = chat_service.update_chat(
        chat.id,
        title="Updated Chat",
        chat={"messages": [{"role": "user", "content": "Hello"}]}
    )
    assert updated_chat.title == "Updated Chat"
    assert updated_chat.chat == {"messages": [{"role": "user", "content": "Hello"}]}
    
    # Delete chat
    chat_service.delete_chat(chat.id)
    assert chat_service.get_chat(chat.id) is None

def test_message_service(message_service: MessageService, chat_service: ChatService, user_service: UserService, db_session: Session):
    # Create user
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    
    # Create chat
    chat = chat_service.create_chat(
        user_id=user.id,
        title="Test Chat",
        chat={"messages": []}
    )
    
    # Create message
    message = message_service.create_message(
        chat_id=chat.id,
        user_id=user.id,
        content="Test message",
        role="user"
    )
    assert message.content == "Test message"
    assert message.role == "user"
    
    # Get message
    retrieved_message = message_service.get_message(message.id)
    assert retrieved_message.id == message.id
    assert retrieved_message.content == message.content
    
    # Update message
    updated_message = message_service.update_message(
        message.id,
        content="Updated message",
        role="assistant"
    )
    assert updated_message.content == "Updated message"
    assert updated_message.role == "assistant"
    
    # Delete message
    message_service.delete_message(message.id)
    assert message_service.get_message(message.id) is None

def test_document_service(document_service: DocumentService, user_service: UserService, db_session: Session):
    # Create user
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    
    # Create document
    document = document_service.create_document(
        user_id=user.id,
        collection_name="test",
        name="test_doc",
        title="Test Document",
        filename="test.txt",
        content="Test content"
    )
    assert document.title == "Test Document"
    assert document.content == "Test content"
    
    # Get document
    retrieved_document = document_service.get_document(document.id)
    assert retrieved_document.id == document.id
    assert retrieved_document.title == document.title
    
    # Update document
    updated_document = document_service.update_document(
        document.id,
        title="Updated Document",
        content="Updated content"
    )
    assert updated_document.title == "Updated Document"
    assert updated_document.content == "Updated content"
    
    # Delete document
    document_service.delete_document(document.id)
    assert document_service.get_document(document.id) is None

def test_tag_service(tag_service: TagService, user_service: UserService, db_session: Session):
    # Create user
    user = user_service.create_user(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    
    # Create tag
    tag = tag_service.create_tag(
        user_id=user.id,
        name="test_tag"
    )
    assert tag.name == "test_tag"
    
    # Get tag
    retrieved_tag = tag_service.get_tag(tag.id)
    assert retrieved_tag.id == tag.id
    assert retrieved_tag.name == tag.name
    
    # Update tag
    updated_tag = tag_service.update_tag(
        tag.id,
        name="updated_tag",
        meta={"color": "blue"}
    )
    assert updated_tag.name == "updated_tag"
    assert updated_tag.meta == {"color": "blue"}
    
    # Delete tag
    tag_service.delete_tag(tag.id)
    assert tag_service.get_tag(tag.id) is None 