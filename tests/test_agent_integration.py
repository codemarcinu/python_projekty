"""
Integration tests for the AI Agent system.
Tests verify the agent's ability to correctly interpret user queries and select appropriate tools.
"""
import pytest
import pytest_asyncio
import asyncio
import csv
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from unittest.mock import patch, MagicMock
from pydantic import BaseModel, Field
from langchain.llms.base import BaseLLM
from langchain.schema import LLMResult, Generation

from core.ai_engine import AIEngine
from core.module_system import get_registered_tools
from langchain_core.language_models.llms import BaseLLM
from langchain_core.outputs import LLMResult, Generation

# --- FAKE LLM ---
class FakeLLM(BaseLLM, BaseModel):
    """Mock LLM for testing."""
    response_map: Dict[str, str] = Field(default_factory=dict)
    
    def _llm_type(self) -> str:
        return "fake"
    
    def _call(self, prompt: Union[str, Dict[str, Any]], stop: Optional[List[str]] = None, **kwargs) -> str:
        """Handle synchronous calls."""
        if isinstance(prompt, dict) and "input" in prompt:
            query = str(prompt["input"])
        else:
            query = str(prompt)
            
        for key, value in self.response_map.items():
            if key in query:
                return value
        return "Final Answer: przepraszam, nie mogę teraz odpowiedzieć."
    
    async def _acall(self, prompt: Union[str, Dict[str, Any]], stop: Optional[List[str]] = None, **kwargs) -> str:
        """Handle asynchronous calls."""
        return self._call(prompt, stop, **kwargs)
    
    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, run_manager: Optional[Any] = None, **kwargs) -> LLMResult:
        """Generate responses for multiple prompts."""
        generations = []
        for prompt in prompts:
            response = self._call(prompt, stop, **kwargs)
            generations.append([Generation(text=response)])
        return LLMResult(generations=generations)

# --- TEST CASE LOADER ---
def load_test_cases() -> List[Dict[str, Any]]:
    """Load test cases from the CSV file."""
    test_cases = []
    csv_path = Path(__file__).parent.parent / "testy_agentów_ai" / "agent_verification_tests.csv"
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            test_cases.append({
                'test_id': row['test_id'],
                'description': row['opis'],
                'query': row['scenariusz'],
                'expected_result': row['oczekiwany_rezultat'],
                'priority': row['priorytet'],
                'category': row['kategoria']
            })
    return test_cases

# --- FIXTURE: AI ENGINE Z FAKE LLM I BEZ WEB_SEARCH_TOOL ---
@pytest_asyncio.fixture
async def ai_engine():
    """Fixture providing an AIEngine instance for testing."""
    # Patch get_registered_tools to filter out web_search_tool
    with patch("core.module_system.get_registered_tools") as mock_get_tools:
        from core.module_system import get_registered_tools as real_get_tools
        tools = {k: v for k, v in real_get_tools().items() if "web_search" not in k}
        mock_get_tools.return_value = tools
        engine = AIEngine()
        # Map scenariusz -> odpowiedź
        response_map = {
            "godzina": "Final Answer: get_current_datetime()",
            "plus": "Final Answer: add(5, 3)",
            "pomnóż": "Final Answer: multiply(4, 7)",
            "dodaj zadanie": "Final Answer: add_task('kupić mleko')",
            "błąd": "Final Answer: Error response"
        }
        engine.llm_manager.llm = FakeLLM(response_map=response_map)
        yield engine

@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", load_test_cases())
async def test_agent_integration(test_case: Dict[str, Any], ai_engine: AIEngine):
    """
    Integration test for agent's tool selection and execution.
    """
    print(f"\nRunning test {test_case['test_id']}: {test_case['description']}")
    response = await ai_engine.process_message(test_case['query'], conversation_id="test-conv")
    assert response is not None, "Agent should return a response"
    # Category-specific assertions
    if test_case['category'] == 'Logika decyzyjna agenta':
        if 'godzina' in test_case['query'].lower():
            assert 'get_current_datetime' in str(response).lower()
        elif any(word in test_case['query'].lower() for word in ['plus', 'pomnóż', 'suma']):
            assert any(tool in str(response).lower() for tool in ['add', 'multiply'])
    elif test_case['category'] == 'Obsługa argumentów':
        if 'pomnóż' in test_case['query'].lower():
            assert 'multiply' in str(response).lower()
        elif 'dodaj zadanie' in test_case['query'].lower():
            assert 'add_task' in str(response).lower()
    print(f"✅ Test {test_case['test_id']} passed")

@pytest.mark.asyncio
async def test_agent_error_handling(ai_engine: AIEngine):
    """Test error handling capabilities of the agent."""
    response = await ai_engine.process_message("Pomnóż tekst przez liczbę", conversation_id="test-conv")
    assert response is not None
    assert "error" in str(response).lower() or "błąd" in str(response).lower()

@pytest.mark.asyncio
async def test_agent_performance(ai_engine: AIEngine):
    """Test agent's performance under load."""
    import time
    
    # Configure mock response for performance tests
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = LLMResult(
        generations=[[Generation(text="Final Answer: Current time is 12:00")]]
    )
    ai_engine.llm_manager.llm = mock_llm
    
    # Test response time for simple query
    start_time = time.time()
    response = await ai_engine.process_message("Która jest godzina?", conversation_id="test-conv")
    end_time = time.time()
    
    response_time = end_time - start_time
    assert response_time < 5.0, f"Response time too slow: {response_time}s"
    
    # Test concurrent requests
    async def make_request():
        return await ai_engine.process_message("Która jest godzina?", conversation_id="test-conv")
    
    # Make 5 concurrent requests
    tasks = [make_request() for _ in range(5)]
    responses = await asyncio.gather(*tasks)
    
    assert all(r is not None for r in responses), "All concurrent requests should succeed"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 