import pytest
from app.schemas.user import UserCreate, UserUpdate, User
from app.schemas.chat import ChatCreate, ChatUpdate, Chat
from app.schemas.message import MessageCreate, MessageUpdate, Message
from app.schemas.document import DocumentCreate, DocumentUpdate, Document
from app.schemas.tag import TagCreate, TagUpdate, Tag
import uuid

def test_user_schemas():
    # Test UserCreate
    user_create = UserCreate(
        name="Test User",
        email="test@example.com",
        password="password123"
    )
    assert user_create.name == "Test User"
    assert user_create.email == "test@example.com"
    assert user_create.password == "password123"
    
    # Test UserUpdate
    user_update = UserUpdate(
        name="Updated User",
        email="updated@example.com"
    )
    assert user_update.name == "Updated User"
    assert user_update.email == "updated@example.com"
    
    # Test User
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        name="Test User",
        email="test@example.com",
        role="user"
    )
    assert user.id == user_id
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.role == "user"

def test_chat_schemas():
    user_id = str(uuid.uuid4())
    
    # Test ChatCreate
    chat_create = ChatCreate(
        title="Test Chat",
        chat={"messages": []}
    )
    assert chat_create.title == "Test Chat"
    assert chat_create.chat == {"messages": []}
    
    # Test ChatUpdate
    chat_update = ChatUpdate(
        title="Updated Chat",
        chat={"messages": [{"role": "user", "content": "Hello"}]}
    )
    assert chat_update.title == "Updated Chat"
    assert chat_update.chat == {"messages": [{"role": "user", "content": "Hello"}]}
    
    # Test Chat
    chat_id = str(uuid.uuid4())
    chat = Chat(
        id=chat_id,
        user_id=user_id,
        title="Test Chat",
        chat={"messages": []}
    )
    assert chat.id == chat_id
    assert chat.user_id == user_id
    assert chat.title == "Test Chat"
    assert chat.chat == {"messages": []}

def test_message_schemas():
    user_id = str(uuid.uuid4())
    chat_id = str(uuid.uuid4())
    
    # Test MessageCreate
    message_create = MessageCreate(
        content="Test message",
        role="user"
    )
    assert message_create.content == "Test message"
    assert message_create.role == "user"
    
    # Test MessageUpdate
    message_update = MessageUpdate(
        content="Updated message",
        role="assistant"
    )
    assert message_update.content == "Updated message"
    assert message_update.role == "assistant"
    
    # Test Message
    message_id = str(uuid.uuid4())
    message = Message(
        id=message_id,
        chat_id=chat_id,
        user_id=user_id,
        content="Test message",
        role="user"
    )
    assert message.id == message_id
    assert message.chat_id == chat_id
    assert message.user_id == user_id
    assert message.content == "Test message"
    assert message.role == "user"

def test_document_schemas():
    user_id = str(uuid.uuid4())
    
    # Test DocumentCreate
    document_create = DocumentCreate(
        collection_name="test",
        name="test_doc",
        title="Test Document",
        filename="test.txt",
        content="Test content"
    )
    assert document_create.collection_name == "test"
    assert document_create.name == "test_doc"
    assert document_create.title == "Test Document"
    assert document_create.filename == "test.txt"
    assert document_create.content == "Test content"
    
    # Test DocumentUpdate
    document_update = DocumentUpdate(
        title="Updated Document",
        content="Updated content"
    )
    assert document_update.title == "Updated Document"
    assert document_update.content == "Updated content"
    
    # Test Document
    document_id = str(uuid.uuid4())
    document = Document(
        id=document_id,
        user_id=user_id,
        collection_name="test",
        name="test_doc",
        title="Test Document",
        filename="test.txt",
        content="Test content"
    )
    assert document.id == document_id
    assert document.user_id == user_id
    assert document.collection_name == "test"
    assert document.name == "test_doc"
    assert document.title == "Test Document"
    assert document.filename == "test.txt"
    assert document.content == "Test content"

def test_tag_schemas():
    user_id = str(uuid.uuid4())
    
    # Test TagCreate
    tag_create = TagCreate(
        name="test_tag"
    )
    assert tag_create.name == "test_tag"
    
    # Test TagUpdate
    tag_update = TagUpdate(
        name="updated_tag",
        meta={"color": "blue"}
    )
    assert tag_update.name == "updated_tag"
    assert tag_update.meta == {"color": "blue"}
    
    # Test Tag
    tag_id = str(uuid.uuid4())
    tag = Tag(
        id=tag_id,
        user_id=user_id,
        name="test_tag",
        meta={"color": "red"}
    )
    assert tag.id == tag_id
    assert tag.user_id == user_id
    assert tag.name == "test_tag"
    assert tag.meta == {"color": "red"} 