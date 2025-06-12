import pytest
from app.services.agents import BaseAgent, ChatAgent, DocumentAgent, TagAgent
from app.services.ollama import OllamaService
from app.models.user import User
from app.models.chat import Chat
from app.models.document import Document
from app.models.tag import Tag
import uuid

@pytest.fixture
def ollama_service():
    return OllamaService()

@pytest.fixture
def base_agent(ollama_service):
    return BaseAgent(ollama_service)

@pytest.fixture
def chat_agent(ollama_service):
    return ChatAgent(ollama_service)

@pytest.fixture
def document_agent(ollama_service):
    return DocumentAgent(ollama_service)

@pytest.fixture
def tag_agent(ollama_service):
    return TagAgent(ollama_service)

def test_base_agent_initialization(base_agent, ollama_service):
    assert base_agent.ollama == ollama_service
    assert isinstance(base_agent.tools, list)
    assert len(base_agent.tools) == 0

def test_base_agent_add_tool(base_agent):
    tool = {
        "name": "test_tool",
        "description": "A test tool",
        "function": lambda x: x
    }
    base_agent.add_tool(tool)
    assert len(base_agent.tools) == 1
    assert base_agent.tools[0]["name"] == "test_tool"

def test_base_agent_process(base_agent):
    message = "What is Python?"
    response = base_agent.process(message)
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_chat_agent_initialization(chat_agent, ollama_service):
    assert chat_agent.ollama == ollama_service
    assert isinstance(chat_agent.tools, list)
    assert len(chat_agent.tools) > 0

def test_chat_agent_process(chat_agent):
    message = "What is Python?"
    response = chat_agent.process(message)
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_chat_agent_process_with_context(chat_agent):
    message = "What is Python?"
    context = "Python is a programming language."
    response = chat_agent.process(message, context=context)
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_chat_agent_process_with_history(chat_agent):
    message = "What is Python?"
    history = [
        {"role": "user", "content": "Tell me about programming languages."},
        {"role": "assistant", "content": "There are many programming languages."}
    ]
    response = chat_agent.process(message, history=history)
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_document_agent_initialization(document_agent, ollama_service):
    assert document_agent.ollama == ollama_service
    assert isinstance(document_agent.tools, list)
    assert len(document_agent.tools) > 0

def test_document_agent_process(document_agent):
    message = "Summarize this document"
    document = Document(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        collection_name="test",
        name="test_doc",
        title="Test Document",
        filename="test.txt",
        content="This is a test document about Python programming language."
    )
    response = document_agent.process(message, document=document)
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_document_agent_process_with_context(document_agent):
    message = "Summarize this document"
    document = Document(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        collection_name="test",
        name="test_doc",
        title="Test Document",
        filename="test.txt",
        content="This is a test document about Python programming language."
    )
    context = "The document is about programming."
    response = document_agent.process(message, document=document, context=context)
    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0

def test_tag_agent_initialization(tag_agent, ollama_service):
    assert tag_agent.ollama == ollama_service
    assert isinstance(tag_agent.tools, list)
    assert len(tag_agent.tools) > 0

def test_tag_agent_process(tag_agent):
    message = "Suggest tags for this document"
    document = Document(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        collection_name="test",
        name="test_doc",
        title="Test Document",
        filename="test.txt",
        content="This is a test document about Python programming language."
    )
    response = tag_agent.process(message, document=document)
    assert response is not None
    assert isinstance(response, list)
    assert len(response) > 0
    for tag in response:
        assert isinstance(tag, str)
        assert len(tag) > 0

def test_tag_agent_process_with_context(tag_agent):
    message = "Suggest tags for this document"
    document = Document(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        collection_name="test",
        name="test_doc",
        title="Test Document",
        filename="test.txt",
        content="This is a test document about Python programming language."
    )
    context = "The document is about programming."
    response = tag_agent.process(message, document=document, context=context)
    assert response is not None
    assert isinstance(response, list)
    assert len(response) > 0
    for tag in response:
        assert isinstance(tag, str)
        assert len(tag) > 0

def test_tag_agent_process_with_existing_tags(tag_agent):
    message = "Suggest additional tags for this document"
    document = Document(
        id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        collection_name="test",
        name="test_doc",
        title="Test Document",
        filename="test.txt",
        content="This is a test document about Python programming language."
    )
    existing_tags = [
        Tag(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            name="python"
        ),
        Tag(
            id=str(uuid.uuid4()),
            user_id=str(uuid.uuid4()),
            name="programming"
        )
    ]
    response = tag_agent.process(message, document=document, existing_tags=existing_tags)
    assert response is not None
    assert isinstance(response, list)
    assert len(response) > 0
    for tag in response:
        assert isinstance(tag, str)
        assert len(tag) > 0
        assert tag not in [t.name for t in existing_tags] 