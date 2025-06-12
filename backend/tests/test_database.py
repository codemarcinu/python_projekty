import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base, get_db
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

def test_database_connection(db_session):
    # Test that we can connect to the database
    assert db_session is not None

def test_create_tables(db_session):
    # Test that all tables are created
    inspector = db_session.get_bind().dialect.inspector
    tables = inspector.get_table_names()
    assert "users" in tables
    assert "chats" in tables
    assert "messages" in tables
    assert "documents" in tables
    assert "tags" in tables
    assert "chat_tags" in tables
    assert "document_tags" in tables

def test_user_relationships(db_session):
    # Create a user
    user = User(
        id=str(uuid.uuid4()),
        name="Test User",
        email="test@example.com",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    
    # Create a chat for the user
    chat = Chat(
        id=str(uuid.uuid4()),
        user_id=user.id,
        title="Test Chat",
        chat={"messages": []}
    )
    db_session.add(chat)
    db_session.commit()
    
    # Create a message for the chat
    message = Message(
        id=str(uuid.uuid4()),
        chat_id=chat.id,
        user_id=user.id,
        content="Test message",
        role="user"
    )
    db_session.add(message)
    db_session.commit()
    
    # Create a document for the user
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
    
    # Create a tag for the user
    tag = Tag(
        id=str(uuid.uuid4()),
        user_id=user.id,
        name="test_tag"
    )
    db_session.add(tag)
    db_session.commit()
    
    # Test relationships
    assert user.chats[0].id == chat.id
    assert user.messages[0].id == message.id
    assert user.documents[0].id == document.id
    assert user.tags[0].id == tag.id
    assert chat.user.id == user.id
    assert chat.messages[0].id == message.id
    assert message.user.id == user.id
    assert message.chat.id == chat.id
    assert document.user.id == user.id
    assert tag.user.id == user.id

def test_chat_tag_relationship(db_session):
    # Create a user
    user = User(
        id=str(uuid.uuid4()),
        name="Test User",
        email="test@example.com",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    
    # Create a chat
    chat = Chat(
        id=str(uuid.uuid4()),
        user_id=user.id,
        title="Test Chat",
        chat={"messages": []}
    )
    db_session.add(chat)
    db_session.commit()
    
    # Create tags
    tag1 = Tag(
        id=str(uuid.uuid4()),
        user_id=user.id,
        name="tag1"
    )
    tag2 = Tag(
        id=str(uuid.uuid4()),
        user_id=user.id,
        name="tag2"
    )
    db_session.add_all([tag1, tag2])
    db_session.commit()
    
    # Add tags to chat
    chat.tags.extend([tag1, tag2])
    db_session.commit()
    
    # Test relationships
    assert len(chat.tags) == 2
    assert chat.tags[0].id == tag1.id
    assert chat.tags[1].id == tag2.id
    assert len(tag1.chats) == 1
    assert len(tag2.chats) == 1
    assert tag1.chats[0].id == chat.id
    assert tag2.chats[0].id == chat.id

def test_document_tag_relationship(db_session):
    # Create a user
    user = User(
        id=str(uuid.uuid4()),
        name="Test User",
        email="test@example.com",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    
    # Create a document
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
    
    # Create tags
    tag1 = Tag(
        id=str(uuid.uuid4()),
        user_id=user.id,
        name="tag1"
    )
    tag2 = Tag(
        id=str(uuid.uuid4()),
        user_id=user.id,
        name="tag2"
    )
    db_session.add_all([tag1, tag2])
    db_session.commit()
    
    # Add tags to document
    document.tags.extend([tag1, tag2])
    db_session.commit()
    
    # Test relationships
    assert len(document.tags) == 2
    assert document.tags[0].id == tag1.id
    assert document.tags[1].id == tag2.id
    assert len(tag1.documents) == 1
    assert len(tag2.documents) == 1
    assert tag1.documents[0].id == document.id
    assert tag2.documents[0].id == document.id

def test_cascade_delete(db_session):
    # Create a user
    user = User(
        id=str(uuid.uuid4()),
        name="Test User",
        email="test@example.com",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    
    # Create a chat
    chat = Chat(
        id=str(uuid.uuid4()),
        user_id=user.id,
        title="Test Chat",
        chat={"messages": []}
    )
    db_session.add(chat)
    db_session.commit()
    
    # Create a message
    message = Message(
        id=str(uuid.uuid4()),
        chat_id=chat.id,
        user_id=user.id,
        content="Test message",
        role="user"
    )
    db_session.add(message)
    db_session.commit()
    
    # Create a document
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
    
    # Create a tag
    tag = Tag(
        id=str(uuid.uuid4()),
        user_id=user.id,
        name="test_tag"
    )
    db_session.add(tag)
    db_session.commit()
    
    # Add tag to chat and document
    chat.tags.append(tag)
    document.tags.append(tag)
    db_session.commit()
    
    # Delete user
    db_session.delete(user)
    db_session.commit()
    
    # Test that all related objects are deleted
    assert db_session.query(User).filter_by(id=user.id).first() is None
    assert db_session.query(Chat).filter_by(id=chat.id).first() is None
    assert db_session.query(Message).filter_by(id=message.id).first() is None
    assert db_session.query(Document).filter_by(id=document.id).first() is None
    assert db_session.query(Tag).filter_by(id=tag.id).first() is None

def test_unique_constraints(db_session):
    # Create a user
    user = User(
        id=str(uuid.uuid4()),
        name="Test User",
        email="test@example.com",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    
    # Try to create another user with the same email
    user2 = User(
        id=str(uuid.uuid4()),
        name="Test User 2",
        email="test@example.com",
        role="user"
    )
    db_session.add(user2)
    
    # Test that it raises an error
    with pytest.raises(Exception):
        db_session.commit()
    
    # Rollback the session
    db_session.rollback()
    
    # Create a document
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
    
    # Try to create another document with the same name in the same collection
    document2 = Document(
        id=str(uuid.uuid4()),
        user_id=user.id,
        collection_name="test",
        name="test_doc",
        title="Test Document 2",
        filename="test2.txt",
        content="Test content 2"
    )
    db_session.add(document2)
    
    # Test that it raises an error
    with pytest.raises(Exception):
        db_session.commit()
    
    # Rollback the session
    db_session.rollback()
    
    # Create a tag
    tag = Tag(
        id=str(uuid.uuid4()),
        user_id=user.id,
        name="test_tag"
    )
    db_session.add(tag)
    db_session.commit()
    
    # Try to create another tag with the same name for the same user
    tag2 = Tag(
        id=str(uuid.uuid4()),
        user_id=user.id,
        name="test_tag"
    )
    db_session.add(tag2)
    
    # Test that it raises an error
    with pytest.raises(Exception):
        db_session.commit()
    
    # Rollback the session
    db_session.rollback() 