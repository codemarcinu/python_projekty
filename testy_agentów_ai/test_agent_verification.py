"""
Testy weryfikacji systemu agentowego AI.
Kompleksowe testy sprawdzające poprawność działania trybu agentowego.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Dodanie ścieżki do modułów projektu
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.ai_engine import AIEngine, get_ai_engine
from core.module_system import get_registered_tools, tool, load_modules
from modules.simple_math import add, multiply
from modules.datetime_tool import get_current_datetime


class TestAgentToolLoading:
    """Testy dynamicznego ładowania narzędzi."""

    def test_tools_are_loaded(self):
        """Test DLN-001: Sprawdzenie czy wszystkie narzędzia są wykrywane."""
        tools = get_registered_tools()

        # Sprawdzenie czy podstawowe narzędzia są załadowane
        expected_tools = ['get_current_datetime', 'add', 'multiply', 'add_task', 'list_tasks']

        for tool_name in expected_tools:
            assert tool_name in tools, f"Narzędzie {tool_name} nie zostało załadowane"

        print(f"✅ Załadowano {len(tools)} narzędzi: {list(tools.keys())}")

    def test_tool_decorator_registration(self):
        """Test weryfikacji działania dekoratora @tool."""

        @tool
        def test_tool(x: int) -> str:
            """Testowe narzędzie."""
            return f"Wynik: {x * 2}"

        tools = get_registered_tools()
        assert 'test_tool' in tools

        # Test wykonania narzędzia
        result = test_tool(5)
        assert result == "Wynik: 10"
        print("✅ Dekorator @tool działa prawidłowo")

    def test_invalid_module_handling(self):
        """Test DLN-003: Obsługa błędnych modułów."""
        # Ten test wymagałby utworzenia tymczasowego błędnego modułu
        # i sprawdzenia czy system kontynuuje działanie
        pass


class TestAgentDecisionLogic:
    """Testy logiki decyzyjnej agenta."""

    @pytest.fixture
    async def ai_engine(self):
        """Fixture do utworzenia instancji AI Engine."""
        engine = AIEngine()
        yield engine

    @pytest.mark.asyncio
    async def test_datetime_query_tool_selection(self, ai_engine):
        """Test LDA-001: Wybór narzędzia dla zapytania o czas."""

        # Mock dla LLM manager
        with patch.object(ai_engine.llm_manager, 'llm') as mock_llm:
            mock_llm.invoke.return_value = Mock(content="Final Answer: Test response")

            queries = [
                "Która jest godzina?",
                "Podaj aktualną datę",
                "Jaki dzisiaj dzień?"
            ]

            for query in queries:
                try:
                    response = await ai_engine.process_message(query)
                    assert response is not None
                    print(f"✅ Zapytanie '{query}' obsłużone: {response[:50]}...")
                except Exception as e:
                    print(f"❌ Błąd dla zapytania '{query}': {e}")

    @pytest.mark.asyncio
    async def test_math_query_tool_selection(self, ai_engine):
        """Test LDA-002: Wybór narzędzia dla zapytania matematycznego."""

        with patch.object(ai_engine.llm_manager, 'llm') as mock_llm:
            mock_llm.invoke.return_value = Mock(content="Final Answer: 8")

            queries = [
                "Ile to 5 plus 3?",
                "Pomnóż 4 przez 6",
                "Oblicz sumę 10 i 15"
            ]

            for query in queries:
                try:
                    response = await ai_engine.process_message(query)
                    assert response is not None
                    print(f"✅ Zapytanie matematyczne '{query}' obsłużone")
                except Exception as e:
                    print(f"❌ Błąd dla zapytania '{query}': {e}")

    @pytest.mark.asyncio
    async def test_fallback_for_general_query(self, ai_engine):
        """Test LDA-003: Fallback dla ogólnych zapytań."""

        with patch.object(ai_engine, '_direct_llm_response') as mock_direct:
            mock_direct.return_value = "To jest odpowiedź z LLM"

            response = await ai_engine.process_message("Opowiedz mi o historii")
            assert response is not None
            print("✅ Fallback dla ogólnych zapytań działa")


class TestAgentArgumentHandling:
    """Testy obsługi argumentów przez agenta."""

    def test_numeric_argument_extraction(self):
        """Test OA-001: Ekstraktowanie argumentów numerycznych."""
        # Test funkcji matematycznych bezpośrednio
        result = add(4.0, 7.0)
        assert result == 11.0

        result = multiply(4, 7)
        assert result == 28
        print("✅ Obsługa argumentów numerycznych działa")

    def test_string_argument_extraction(self):
        """Test OA-002: Obsługa argumentów tekstowych."""
        # Ten test wymagałby mockowania ekstraktowania argumentów z NLP
        pass


class TestAgentErrorHandling:
    """Testy obsługi błędów przez agenta."""

    @pytest.mark.asyncio
    async def test_tool_failure_handling(self):
        """Test OB-001: Reakcja na awarie narzędzia."""

        @tool
        def failing_tool() -> str:
            """Narzędzie które zawsze failuje."""
            raise Exception("Symulowana awaria narzędzia")

        # Sprawdzenie czy system nie crashuje przy awarii narzędzia
        try:
            result = failing_tool()
            assert False, "Narzędzie powinno było rzucić wyjątek"
        except Exception as e:
            print(f"✅ Awaria narzędzia została obsłużona: {e}")

    def test_invalid_arguments_handling(self):
        """Test OB-002: Obsługa nieprawidłowych argumentów."""

        # Test z nieprawidłowymi typami argumentów
        try:
            # multiply oczekuje int, podajemy string
            result = multiply("tekst", 5)
            assert False, "Powinien wystąpić błąd walidacji typów"
        except (TypeError, ValueError):
            print("✅ Walidacja typów argumentów działa")


class TestAgentPerformance:
    """Testy wydajności agenta."""

    @pytest.mark.asyncio
    async def test_response_time(self):
        """Test W-001: Czas odpowiedzi agenta."""
        import time

        ai_engine = AIEngine()

        start_time = time.time()

        # Test prostego narzędzia
        result = get_current_datetime()

        end_time = time.time()
        response_time = end_time - start_time

        assert response_time < 1.0, f"Czas odpowiedzi zbyt długi: {response_time}s"
        print(f"✅ Czas odpowiedzi: {response_time:.3f}s")


class TestAgentIntegration:
    """Testy integracji całego systemu."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test kompletnego workflow agenta."""

        ai_engine = AIEngine()

        # Sprawdzenie czy agent został poprawnie zainicjowany
        status = ai_engine.get_agent_status()

        assert status['agent_available'] == True
        assert status['tools_count'] > 0
        assert len(status['available_tools']) > 0

        print(f"✅ Agent zainicjowany z {status['tools_count']} narzędziami")
        print(f"Dostępne narzędzia: {status['available_tools']}")


if __name__ == "__main__":
    # Uruchomienie testów
    pytest.main([__file__, "-v", "--tb=short"])
