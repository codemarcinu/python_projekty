import pytest
from datetime import datetime, timedelta
import json
import os
import shutil
from pathlib import Path

from app.services.conversation.service import ConversationService, Message, Conversation
from app.services.conversation.exceptions import (
    ConversationNotFoundError,
    MessageLimitExceededError,
    StorageError
)

@pytest.fixture
def temp_storage_dir(tmp_path):
    """Create a temporary storage directory for tests."""
    storage_dir = tmp_path / "conversations"
    storage_dir.mkdir()
    yield storage_dir
    shutil.rmtree(storage_dir)

@pytest.fixture
def conversation_service(temp_storage_dir):
    """Create a conversation service instance."""
    return ConversationService(storage_dir=temp_storage_dir)

@pytest.mark.asyncio
async def test_create_conversation(conversation_service):
    """Test creating a new conversation."""
    # Create conversation
    conversation = await conversation_service.create_conversation(
        title="Test Conversation",
        initial_message="Hello"
    )
    
    # Check conversation properties
    assert conversation.id is not None
    assert conversation.title == "Test Conversation"
    assert len(conversation.messages) == 1
    assert conversation.messages[0].content == "Hello"
    assert conversation.messages[0].role == "user"
    assert isinstance(conversation.created_at, datetime)
    assert isinstance(conversation.updated_at, datetime)

@pytest.mark.asyncio
async def test_get_conversation(conversation_service):
    """Test retrieving a conversation."""
    # Create conversation
    created = await conversation_service.create_conversation(
        title="Test Conversation",
        initial_message="Hello"
    )
    
    # Get conversation
    retrieved = await conversation_service.get_conversation(created.id)
    
    # Check if retrieved matches created
    assert retrieved.id == created.id
    assert retrieved.title == created.title
    assert len(retrieved.messages) == len(created.messages)
    assert retrieved.messages[0].content == created.messages[0].content

@pytest.mark.asyncio
async def test_get_nonexistent_conversation(conversation_service):
    """Test retrieving a nonexistent conversation."""
    with pytest.raises(ConversationNotFoundError):
        await conversation_service.get_conversation("nonexistent-id")

@pytest.mark.asyncio
async def test_add_message(conversation_service):
    """Test adding a message to a conversation."""
    # Create conversation
    conversation = await conversation_service.create_conversation(
        title="Test Conversation",
        initial_message="Hello"
    )
    
    # Add message
    updated = await conversation_service.add_message(
        conversation_id=conversation.id,
        content="How are you?",
        role="user"
    )
    
    # Check message was added
    assert len(updated.messages) == 2
    assert updated.messages[1].content == "How are you?"
    assert updated.messages[1].role == "user"
    assert isinstance(updated.messages[1].timestamp, datetime)

@pytest.mark.asyncio
async def test_message_limit(conversation_service):
    """Test message limit enforcement."""
    # Create conversation
    conversation = await conversation_service.create_conversation(
        title="Test Conversation",
        initial_message="Hello"
    )
    
    # Add messages up to limit
    for i in range(conversation_service.MAX_MESSAGES - 1):
        conversation = await conversation_service.add_message(
            conversation_id=conversation.id,
            content=f"Message {i}",
            role="user"
        )
    
    # Try to add one more message
    with pytest.raises(MessageLimitExceededError):
        await conversation_service.add_message(
            conversation_id=conversation.id,
            content="One too many",
            role="user"
        )

@pytest.mark.asyncio
async def test_delete_conversation(conversation_service):
    """Test deleting a conversation."""
    # Create conversation
    conversation = await conversation_service.create_conversation(
        title="Test Conversation",
        initial_message="Hello"
    )
    
    # Delete conversation
    await conversation_service.delete_conversation(conversation.id)
    
    # Verify deletion
    with pytest.raises(ConversationNotFoundError):
        await conversation_service.get_conversation(conversation.id)

@pytest.mark.asyncio
async def test_list_conversations(conversation_service):
    """Test listing conversations."""
    # Create multiple conversations
    conversations = []
    for i in range(3):
        conversation = await conversation_service.create_conversation(
            title=f"Test Conversation {i}",
            initial_message=f"Hello {i}"
        )
        conversations.append(conversation)
    
    # List conversations
    listed = await conversation_service.list_conversations()
    
    # Check results
    assert len(listed) == 3
    assert all(c.id in [conv.id for conv in conversations] for c in listed)
    assert all(c.title.startswith("Test Conversation") for c in listed)

@pytest.mark.asyncio
async def test_cleanup_old_conversations(conversation_service):
    """Test cleaning up old conversations."""
    # Create old conversation
    old_conversation = await conversation_service.create_conversation(
        title="Old Conversation",
        initial_message="Hello"
    )
    old_conversation.created_at = datetime.now() - timedelta(days=2)
    await conversation_service._save_conversation(old_conversation)
    
    # Create new conversation
    new_conversation = await conversation_service.create_conversation(
        title="New Conversation",
        initial_message="Hello"
    )
    
    # Cleanup old conversations
    await conversation_service.cleanup_old_conversations(max_age_days=1)
    
    # Verify cleanup
    listed = await conversation_service.list_conversations()
    assert len(listed) == 1
    assert listed[0].id == new_conversation.id

@pytest.mark.asyncio
async def test_storage_error(conversation_service, temp_storage_dir):
    """Test storage error handling."""
    # Remove storage directory to simulate error
    shutil.rmtree(temp_storage_dir)
    
    # Try to create conversation
    with pytest.raises(StorageError):
        await conversation_service.create_conversation(
            title="Test Conversation",
            initial_message="Hello"
        )

@pytest.mark.asyncio
async def test_conversation_serialization(conversation_service):
    """Test conversation serialization and deserialization."""
    # Create conversation
    conversation = await conversation_service.create_conversation(
        title="Test Conversation",
        initial_message="Hello"
    )
    
    # Add some messages
    conversation = await conversation_service.add_message(
        conversation_id=conversation.id,
        content="How are you?",
        role="user"
    )
    conversation = await conversation_service.add_message(
        conversation_id=conversation.id,
        content="I'm good, thanks!",
        role="assistant"
    )
    
    # Get conversation from storage
    retrieved = await conversation_service.get_conversation(conversation.id)
    
    # Check serialization
    assert retrieved.id == conversation.id
    assert retrieved.title == conversation.title
    assert len(retrieved.messages) == 3
    assert retrieved.messages[0].content == "Hello"
    assert retrieved.messages[1].content == "How are you?"
    assert retrieved.messages[2].content == "I'm good, thanks!"
    assert retrieved.messages[0].role == "user"
    assert retrieved.messages[1].role == "user"
    assert retrieved.messages[2].role == "assistant"

@pytest.mark.asyncio
async def test_conversation_metadata(conversation_service):
    """Test conversation metadata handling."""
    # Create conversation with metadata
    metadata = {
        "source": "test",
        "tags": ["test", "conversation"],
        "priority": "high"
    }
    conversation = await conversation_service.create_conversation(
        title="Test Conversation",
        initial_message="Hello",
        metadata=metadata
    )
    
    # Check metadata
    assert conversation.metadata == metadata
    
    # Update metadata
    updated_metadata = {**metadata, "priority": "low"}
    conversation = await conversation_service.update_conversation_metadata(
        conversation_id=conversation.id,
        metadata=updated_metadata
    )
    
    # Check updated metadata
    assert conversation.metadata == updated_metadata 