import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message
from app.models.document import Document
from app.models.tag import Tag
import uuid

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="session")
def SessionLocal():
    return sessionmaker(autocommit=False, autoflush=False, bind=engine())

@pytest.fixture(scope="function")
def db_session(SessionLocal):
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_create_user(db_session):
    user = User(
        id=str(uuid.uuid4()),
        name="Test User",
        email="test@example.com",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.name == "Test User"
    assert user.email == "test@example.com"
    assert user.role == "user"

def test_create_chat(db_session):
    user = User(
        id=str(uuid.uuid4()),
        name="Test User",
        email="test@example.com",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    
    chat = Chat(
        id=str(uuid.uuid4()),
        user_id=user.id,
        title="Test Chat",
        chat={"messages": []}
    )
    db_session.add(chat)
    db_session.commit()
    
    assert chat.id is not None
    assert chat.user_id == user.id
    assert chat.title == "Test Chat"

def test_create_message(db_session):
    user = User(
        id=str(uuid.uuid4()),
        name="Test User",
        email="test@example.com",
        role="user"
    )
    db_session.add(user)
    
    chat = Chat(
        id=str(uuid.uuid4()),
        user_id=user.id,
        title="Test Chat",
        chat={"messages": []}
    )
    db_session.add(chat)
    db_session.commit()
    
    message = Message(
        id=str(uuid.uuid4()),
        chat_id=chat.id,
        user_id=user.id,
        content="Test message",
        role="user"
    )
    db_session.add(message)
    db_session.commit()
    
    assert message.id is not None
    assert message.chat_id == chat.id
    assert message.user_id == user.id
    assert message.content == "Test message"
    assert message.role == "user"

def test_create_document(db_session):
    user = User(
        id=str(uuid.uuid4()),
        name="Test User",
        email="test@example.com",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    
    document = Document(
        id=str(uuid.uuid4()),
        user_id=user.id,
        collection_name="test",
        name="test_doc",
        title="Test Document",
        filename="test.txt",
        content="Test content"
    )
    db_session.add(document)
    db_session.commit()
    
    assert document.id is not None
    assert document.user_id == user.id
    assert document.collection_name == "test"
    assert document.name == "test_doc"
    assert document.title == "Test Document"
    assert document.filename == "test.txt"
    assert document.content == "Test content"

def test_create_tag(db_session):
    user = User(
        id=str(uuid.uuid4()),
        name="Test User",
        email="test@example.com",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    
    tag = Tag(
        id=str(uuid.uuid4()),
        user_id=user.id,
        name="test_tag"
    )
    db_session.add(tag)
    db_session.commit()
    
    assert tag.id is not None
    assert tag.user_id == user.id
    assert tag.name == "test_tag" 