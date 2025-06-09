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
        
        # Ustawienie promptu systemowego
        self.system_prompt = f"""Jesteś pomocnym asystentem AI z dostępem do narzędzi.
OTO DOSTĘPNE NARZĘDZIA:
{self.tools_description}

ZASADY POSTĘPOWANIA:
- Kiedy chcesz użyć narzędzia, Twoja odpowiedź MUSI zaczynać się od specjalnego znacznika `TOOL_CALL::`, po którym natychmiast następuje obiekt JSON.
- Przykład: `TOOL_CALL::{{"tool": "nazwa_narzedzia", "args": {{"arg1": "wartosc1"}}}}`
- NIE WOLNO Ci dodawać żadnego tekstu przed znacznikiem `TOOL_CALL::`.
- Do zarządzania listą zadań ZAWSZE używaj dostępnych narzędzi.
- Jeśli nie używasz narzędzia, po prostu odpowiedz użytkownikowi w formie zwykłego tekstu.
"""

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

    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Próbuje sparsować odpowiedź LLM jako JSON po znaczniku TOOL_CALL::.
        
        Args:
            response (str): Odpowiedź od modelu LLM.
            
        Returns:
            Optional[Dict[str, Any]]: Sparsowany JSON lub None jeśli parsowanie się nie powiodło.
        """
        if not response.startswith("TOOL_CALL::"):
            return None
            
        try:
            json_str = response[len("TOOL_CALL::"):].strip()
            return json.loads(json_str)
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
        system_message = {"role": "system", "content": self.system_prompt}
        full_history = [system_message] + conversation_history
        
        # Wywołanie LLM
        llm_response = self.llm.generate_response(full_history)
        
        # Sprawdzenie czy odpowiedź zawiera wywołanie narzędzia
        if llm_response.startswith("TOOL_CALL::"):
            # Próba parsowania odpowiedzi jako JSON
            parsed_response = self._parse_llm_response(llm_response)
            
            if parsed_response and "tool" in parsed_response:
                try:
                    tool_name = parsed_response["tool"]
                    tool_args = parsed_response.get("args", {})
                    
                    # Wywołanie narzędzia i bezpośrednie zwrócenie wyniku
                    tool_result = get_tool(tool_name)(**tool_args)
                    return str(tool_result)
                    
                except Exception as e:
                    return f"Wystąpił błąd podczas wykonywania narzędzia: {str(e)}"
        
        # Jeśli odpowiedź nie zawiera wywołania narzędzia, zwracamy ją bezpośrednio
        return llm_response
