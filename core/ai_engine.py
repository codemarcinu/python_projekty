"""
Moduł zawierający główny silnik AI odpowiedzialny za zarządzanie logiką agenta AI.

Ten moduł implementuje klasę AIEngine, która koordynuje działanie modelu językowego
z systemem wtyczek, umożliwiając agentowi wykonywanie zadań i odpowiadanie użytkownikowi.
"""

from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from .llm_manager import LLMManager
from .plugin_system import load_plugins, get_tool, get_available_tools


class AIEngine:
    """Główny silnik AI zarządzający logiką agenta i integracją z narzędziami."""

    def __init__(self, plugins_dir: str = "plugins") -> None:
        """Inicjalizuje silnik AI.
        
        Args:
            plugins_dir (str): Ścieżka do katalogu zawierającego wtyczki.
        """
        # Inicjalizacja menedżera LLM
        self.llm = LLMManager()
        
        # Ładowanie wtyczek
        load_plugins(plugins_dir)
        
        # Przygotowanie opisu narzędzi dla promptu
        self.tools_description = self._prepare_tools_prompt()

    def _prepare_tools_prompt(self) -> str:
        """Przygotowuje opis dostępnych narzędzi w formacie tekstowym.
        
        Returns:
            str: Sformatowany opis narzędzi do użycia w promptcie.
        """
        tools_description = ""
        for tool_name in self._get_available_tools():
            tool = get_tool(tool_name)
            tools_description += f"- {tool_name}: {tool.__doc__ or 'Brak opisu'}\n"
        return tools_description

    def _get_available_tools(self) -> List[str]:
        """Zwraca listę nazw dostępnych narzędzi.
        
        Returns:
            List[str]: Lista nazw narzędzi.
        """
        return get_available_tools()

    def _create_system_prompt(self) -> str:
        """Tworzy prompt systemowy dla modelu LLM.
        
        Returns:
            str: Prompt systemowy zawierający instrukcje i opis narzędzi.
        """
        return f"""Jesteś pomocnym asystentem AI. Masz dostęp do zestawu narzędzi.

OTO DOSTĘPNE NARZĘDZIA:
{self.tools_description}

ZASADY POSTĘPOWANIA:
- Kiedy chcesz użyć narzędzia, ZAWSZE odpowiadaj TYLKO I WYŁĄCZNIE obiektem JSON w formacie: {{"tool": "nazwa_narzedzia", "args": {{"arg1": "wartosc1", ...}}}}.
- NIE WOLNO Ci dodawać żadnego tekstu przed ani po obiekcie JSON. Twoja odpowiedź musi być czystym JSON-em.
- Jeśli nie chcesz używać narzędzia, odpowiedz użytkownikowi w normalny sposób, jako zwykły tekst.

PRZYKŁAD UŻYCIA NARZĘDZIA:
Pytanie użytkownika: Ile to jest 5 dodać 7?
Twoja odpowiedź (JSON): {{"tool": "add", "args": {{"a": 5, "b": 7}}}}"""

    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Próbuje sparsować odpowiedź LLM jako JSON.
        
        Args:
            response (str): Odpowiedź od modelu LLM.
            
        Returns:
            Optional[Dict[str, Any]]: Sparsowany JSON lub None jeśli parsowanie się nie powiodło.
        """
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return None

    def process_turn(self, conversation_history: List[Dict[str, str]]) -> str:
        """Przetwarza pojedynczą turę konwersacji.
        
        Args:
            conversation_history (List[Dict[str, str]]): Historia konwersacji w formacie
                listy słowników z kluczami 'role' i 'content'.
                
        Returns:
            str: Odpowiedź dla użytkownika.
        """
        # Dodanie promptu systemowego do historii
        system_message = {"role": "system", "content": self._create_system_prompt()}
        full_history = [system_message] + conversation_history
        
        # Pierwsze wywołanie LLM
        llm_response = self.llm.generate_response(full_history)
        
        # Próba parsowania odpowiedzi jako JSON
        parsed_response = self._parse_llm_response(llm_response)
        
        if parsed_response and "tool" in parsed_response:
            # Obsługa wywołania narzędzia
            try:
                tool_name = parsed_response["tool"]
                tool_args = parsed_response.get("args", {})
                
                # Wywołanie narzędzia
                tool_result = get_tool(tool_name)(**tool_args)
                
                # Dodanie informacji o wyniku narzędzia do historii
                tool_message = {
                    "role": "system",
                    "content": f"Wynik narzędzia {tool_name}: {str(tool_result)}"
                }
                full_history.append(tool_message)
                
                # Drugie wywołanie LLM z wynikiem narzędzia
                final_response = self.llm.generate_response(full_history)
                return final_response
                
            except Exception as e:
                return f"Wystąpił błąd podczas wykonywania narzędzia: {str(e)}"
        
        # Jeśli odpowiedź nie jest JSON-em, zwracamy ją bezpośrednio
        return llm_response
