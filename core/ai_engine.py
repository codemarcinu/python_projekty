"""
Moduł zawierający główny silnik AI odpowiedzialny za zarządzanie logiką agenta AI.

Ten moduł implementuje klasę AIEngine, która koordynuje działanie modelu językowego
z systemem wtyczek, umożliwiając agentowi wykonywanie zadań i odpowiadanie użytkownikowi.
"""

import json
import inspect
from .llm_manager import LLMManager
from .plugin_system import load_plugins, get_tool, _tools
from typing import List, Dict, Any


class AIEngine:
    """
    Główny silnik AI, działający w oparciu o architekturę "Routera Narzędzi".
    Najpierw decyduje, czy użyć narzędzia, a dopiero potem wykonuje akcję.
    """

    def __init__(self):
        load_plugins("plugins")
        self.tools_description = self._get_formatted_tools_description()
        self.llm = LLMManager()
        print("Silnik AI (Super-Prosty Router) został zainicjalizowany.")

    def _get_formatted_tools_description(self) -> str:
        """Tworzy opis narzędzi dla promptu routera."""
        descriptions = []
        for name, func in _tools.items():
            docstring = func.__doc__.strip() if func.__doc__ else "Brak opisu."
            descriptions.append(f"- {name}: {docstring}")
        return "\n".join(descriptions)

    def _choose_tool(self, user_prompt: str) -> str:
        # OSTATECZNY, NAJPROSTSZY MOŻLIWY PROMPT
        tool_names = ", ".join(_tools.keys())
        prompt = f"""Odpowiedz jednym słowem. Które z tych narzędzi: [{tool_names}, None] najlepiej pasuje do prośby użytkownika?

        Prośba: "{user_prompt}"
        Narzędzie:"""

        response = self.llm.generate_response([{'role': 'user', 'content': prompt}])
        
        # BARDZIEJ ODPORNA METODA PARSOWANIA
        response_lower = response.lower().strip().replace('"', '').replace("'", "").replace(".", "")

        # Sprawdźmy, czy odpowiedź to DOKŁADNIE nazwa jednego z narzędzi
        for tool_name in _tools:
            if tool_name.lower() in response_lower:
                print(f"DEBUG: Router wybrał narzędzie: {tool_name}")
                return tool_name

        print(f"DEBUG: Router nie wybrał żadnego narzędzia (odpowiedź AI: '{response}')")
        return "None"

    def _get_tool_args(self, tool_name: str, user_prompt: str) -> Dict[str, Any]:
        """Etap 2a: Wydobycie argumentów dla wybranego narzędzia."""
        target_tool = get_tool(tool_name)
        arg_spec = inspect.getfullargspec(target_tool)
        
        prompt = f"""Twoim zadaniem jest wydobycie argumentów dla narzędzia '{tool_name}' z prośby użytkownika.
        Wymagane argumenty: {arg_spec.args}
        Prośba użytkownika: "{user_prompt}"
        Odpowiedz TYLKO I WYŁĄCZNIE poprawnym obiektem JSON.
        """
        response = self.llm.generate_response([{'role': 'user', 'content': prompt}])
        try:
            cleaned_json = response[response.find('{'):response.rfind('}')+1]
            args = json.loads(cleaned_json)
            print(f"DEBUG: Router uzyskał argumenty: {args}")
            return args
        except json.JSONDecodeError:
            print(f"BŁĄD: Nie udało się sparsować argumentów JSON: {response}")
            return {} # Zwróć pusty słownik, jeśli nie ma argumentów

    def process_turn(self, conversation_history: List[Dict[str, str]]) -> str:
        """Główna metoda przetwarzająca turę rozmowy."""
        user_prompt = conversation_history[-1]['content']
        
        # ETAP 1: ROUTING
        chosen_tool_name = self._choose_tool(user_prompt)

        # ETAP 2: WYKONANIE LUB ROZMOWA
        if chosen_tool_name != "None":
            tool_args = self._get_tool_args(chosen_tool_name, user_prompt)
            tool_function = get_tool(chosen_tool_name)
            try:
                result = tool_function(**tool_args)
                return str(result)
            except Exception as e:
                return f"Błąd podczas wykonywania narzędzia {chosen_tool_name}: {e}"
        else:
            # Jeśli żadne narzędzie nie zostało wybrane, prowadź normalną rozmowę
            return self.llm.generate_response(conversation_history)
