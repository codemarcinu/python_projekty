import pytest
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime

from app.services.agents.base import BaseAgent, AgentState, AgentResponse
from app.services.agents.specialized import ChatAgent, ResearchAgent, CodingAgent
from app.services.agents.orchestrator import AgentOrchestrator, AgentConfig
from app.services.ollama.service import OllamaService
from app.core.config import settings

@pytest.fixture
def mock_ollama_service():
    """Create a mock Ollama service."""
    service = AsyncMock(spec=OllamaService)
    service.generate_with_context.return_value = "Mock response"
    return service

@pytest.fixture
def chat_agent(mock_ollama_service):
    """Create a chat agent instance."""
    return ChatAgent(
        ollama_service=mock_ollama_service,
        model_name=settings.DEFAULT_CHAT_MODEL
    )

@pytest.fixture
def research_agent(mock_ollama_service):
    """Create a research agent instance."""
    return ResearchAgent(
        ollama_service=mock_ollama_service,
        model_name=settings.DEFAULT_CHAT_MODEL
    )

@pytest.fixture
def coding_agent(mock_ollama_service):
    """Create a coding agent instance."""
    return CodingAgent(
        ollama_service=mock_ollama_service,
        model_name=settings.DEFAULT_CODE_MODEL
    )

@pytest.fixture
def orchestrator(mock_ollama_service):
    """Create an agent orchestrator instance."""
    return AgentOrchestrator(ollama_service=mock_ollama_service)

@pytest.mark.asyncio
async def test_chat_agent_process(chat_agent, mock_ollama_service):
    """Test chat agent message processing."""
    # Process message
    response = await chat_agent.process("Hello")
    
    # Check response
    assert response.content == "Mock response"
    assert isinstance(response.state, AgentState)
    assert response.metadata["type"] == "chat"
    
    # Check state
    assert len(response.state.messages) == 2  # User message + assistant response
    assert response.state.messages[0]["role"] == "user"
    assert response.state.messages[0]["content"] == "Hello"
    assert response.state.messages[1]["role"] == "assistant"
    assert response.state.messages[1]["content"] == "Mock response"
    
    # Verify Ollama service call
    mock_ollama_service.generate_with_context.assert_called_once()

@pytest.mark.asyncio
async def test_research_agent_process(research_agent, mock_ollama_service):
    """Test research agent query processing."""
    # Process query
    response = await research_agent.process("Tell me about AI")
    
    # Check response
    assert response.content == "Mock response"
    assert isinstance(response.state, AgentState)
    assert response.metadata["type"] == "research"
    assert "sources" in response.metadata
    
    # Check state
    assert len(response.state.messages) == 2
    assert response.state.messages[0]["role"] == "user"
    assert response.state.messages[0]["content"] == "Tell me about AI"

@pytest.mark.asyncio
async def test_coding_agent_process(coding_agent, mock_ollama_service):
    """Test coding agent request processing."""
    # Process request
    response = await coding_agent.process("Write a Python function")
    
    # Check response
    assert response.content == "Mock response"
    assert isinstance(response.state, AgentState)
    assert response.metadata["type"] == "code"
    assert "language" in response.metadata
    assert "execution_result" in response.metadata
    
    # Check state
    assert len(response.state.messages) == 2
    assert response.state.messages[0]["role"] == "user"
    assert response.state.messages[0]["content"] == "Write a Python function"

@pytest.mark.asyncio
async def test_orchestrator_process(orchestrator, mock_ollama_service):
    """Test orchestrator message processing."""
    # Process message with default agent
    response = await orchestrator.process("Hello")
    
    # Check response
    assert response.content == "Mock response"
    assert orchestrator.state.current_agent == "ChatAgent"
    
    # Check workflow history
    assert len(orchestrator.state.workflow_history) == 1
    history_entry = orchestrator.state.workflow_history[0]
    assert history_entry["message"] == "Hello"
    assert history_entry["response"] == "Mock response"
    assert history_entry["agent"] == "ChatAgent"

@pytest.mark.asyncio
async def test_orchestrator_switch_agent(orchestrator):
    """Test switching between agents."""
    # Switch to research agent
    await orchestrator.switch_agent("research")
    assert orchestrator.state.current_agent == "ResearchAgent"
    
    # Process message
    response = await orchestrator.process("Research query")
    assert response.metadata["type"] == "research"
    
    # Switch to coding agent
    await orchestrator.switch_agent("code")
    assert orchestrator.state.current_agent == "CodingAgent"
    
    # Process message
    response = await orchestrator.process("Code request")
    assert response.metadata["type"] == "code"

@pytest.mark.asyncio
async def test_orchestrator_reset(orchestrator):
    """Test resetting orchestrator state."""
    # Process some messages
    await orchestrator.process("Message 1")
    await orchestrator.process("Message 2")
    
    # Reset state
    await orchestrator.reset()
    
    # Check state
    assert len(orchestrator.state.workflow_history) == 0
    for agent_state in orchestrator.state.agent_states.values():
        assert len(agent_state.messages) == 0

@pytest.mark.asyncio
async def test_agent_state_persistence(chat_agent):
    """Test agent state persistence."""
    # Process initial message
    response1 = await chat_agent.process("First message")
    state1 = response1.state
    
    # Process follow-up message
    response2 = await chat_agent.process("Follow-up", state=state1)
    
    # Check state persistence
    assert len(response2.state.messages) == 4  # 2 messages + 2 responses
    assert response2.state.messages[0]["content"] == "First message"
    assert response2.state.messages[2]["content"] == "Follow-up"

@pytest.mark.asyncio
async def test_orchestrator_custom_config(mock_ollama_service):
    """Test orchestrator with custom agent configurations."""
    configs = [
        AgentConfig(
            type="chat",
            model_name="custom-model",
            system_prompt="Custom prompt",
            metadata={"custom_param": "value"}
        )
    ]
    
    orchestrator = AgentOrchestrator(
        ollama_service=mock_ollama_service,
        configs=configs
    )
    
    # Check agent initialization
    assert "chat" in orchestrator.agents
    assert orchestrator.agents["chat"].model_name == "custom-model"
    assert orchestrator.agents["chat"].system_prompt == "Custom prompt"

@pytest.mark.asyncio
async def test_error_handling(chat_agent, mock_ollama_service):
    """Test error handling in agents."""
    # Mock error
    mock_ollama_service.generate_with_context.side_effect = Exception("Test error")
    
    # Process message
    with pytest.raises(Exception):
        await chat_agent.process("Error test")
    
    # Check state
    assert len(chat_agent.state.messages) == 1  # Only user message
    assert chat_agent.state.messages[0]["content"] == "Error test" 