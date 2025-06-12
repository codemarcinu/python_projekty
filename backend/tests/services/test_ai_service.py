import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.ai.service import AIService
from app.services.ai.exceptions import (
    AIServiceError, ModelNotFoundError, ProcessingError,
    RAGError, VectorStoreError, AgentError, ToolExecutionError
)
from app.services.conversation.service import ConversationService

@pytest.fixture
def mock_conversation_service():
    """Create a mock conversation service."""
    service = Mock(spec=ConversationService)
    service.get_conversation = AsyncMock()
    service.add_message = AsyncMock()
    return service

@pytest.fixture
def mock_settings():
    """Create mock settings."""
    return {
        "rag": {
            "vector_db_path": "test_data/vector_db",
            "embedding_model": "test-model"
        }
    }

@pytest.fixture
def ai_service(mock_conversation_service, mock_settings):
    """Create an AI service instance with mocked dependencies."""
    with patch("app.services.ai.service.get_settings", return_value=mock_settings):
        service = AIService(
            conversation_service=mock_conversation_service,
            settings=mock_settings
        )
        return service

@pytest.mark.asyncio
async def test_process_message_success(ai_service, mock_conversation_service):
    """Test successful message processing."""
    # Setup
    conversation_id = "test-conv"
    message = "Hello, AI!"
    mock_conversation = Mock()
    mock_conversation_service.get_conversation.return_value = mock_conversation
    
    # Mock LLM response
    ai_service.llm = Mock()
    ai_service.llm.invoke.return_value = "Hello, human!"
    
    # Execute
    response = await ai_service.process_message(message, conversation_id)
    
    # Assert
    assert response == "Hello, human!"
    mock_conversation_service.get_conversation.assert_called_once_with(conversation_id)
    mock_conversation_service.add_message.assert_called()

@pytest.mark.asyncio
async def test_process_message_conversation_not_found(ai_service, mock_conversation_service):
    """Test message processing with non-existent conversation."""
    # Setup
    mock_conversation_service.get_conversation.return_value = None
    
    # Execute and Assert
    with pytest.raises(ProcessingError):
        await ai_service.process_message("test", "non-existent")

@pytest.mark.asyncio
async def test_process_message_llm_error(ai_service, mock_conversation_service):
    """Test message processing with LLM error."""
    # Setup
    mock_conversation = Mock()
    mock_conversation_service.get_conversation.return_value = mock_conversation
    
    ai_service.llm = Mock()
    ai_service.llm.invoke.side_effect = Exception("LLM error")
    
    # Execute and Assert
    with pytest.raises(ProcessingError):
        await ai_service.process_message("test", "test-conv")

@pytest.mark.asyncio
async def test_list_models(ai_service):
    """Test listing available models."""
    # Execute
    models = await ai_service.list_models()
    
    # Assert
    assert isinstance(models, list)
    assert "gemma3:12b" in models

@pytest.mark.asyncio
async def test_get_agent_status(ai_service):
    """Test getting agent status."""
    # Execute
    status = await ai_service.get_agent_status()
    
    # Assert
    assert isinstance(status, dict)
    assert "agent_initialized" in status
    assert "tools_count" in status
    assert "rag_available" in status
    assert "vector_store_available" in status

def test_setup_llm_error():
    """Test LLM setup error handling."""
    with patch("app.services.ai.service.OllamaLLM", side_effect=Exception("LLM error")):
        with pytest.raises(ModelNotFoundError):
            AIService(Mock(spec=ConversationService))

def test_setup_rag_error():
    """Test RAG setup error handling."""
    with patch("app.services.ai.service.HuggingFaceEmbeddings", side_effect=Exception("RAG error")):
        with pytest.raises(RAGError):
            AIService(Mock(spec=ConversationService))

def test_setup_agent_error():
    """Test agent setup error handling."""
    with patch("app.services.ai.service.AIService._load_tools", side_effect=Exception("Agent error")):
        with pytest.raises(AgentError):
            AIService(Mock(spec=ConversationService)) 