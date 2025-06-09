"""
Moduł zawierający główny silnik AI odpowiedzialny za zarządzanie logiką agenta AI.

Ten moduł implementuje klasę AIEngine, która koordynuje działanie modelu językowego
z systemem wtyczek, umożliwiając agentowi wykonywanie zadań i odpowiadanie użytkownikowi.
"""

import json
import inspect
from .llm_manager import LLMManager
from .plugin_system import load_plugins, get_tool, _tools
from .tool_models import WeatherArgs, AddTaskArgs, ListTasksArgs, TaskIdArgs, MathArgs
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
        print("AI Engine (Context-Aware Router) has been initialized.")

    def _get_formatted_tools_description(self) -> str:
        """Tworzy opis narzędzi dla promptu routera."""
        descriptions = []
        for name, func in _tools.items():
            docstring = func.__doc__.strip() if func.__doc__ else "No description available."
            descriptions.append(f"- {name}: {docstring}")
        return "\n".join(descriptions)

    def _choose_tool(self, conversation_history: List[Dict[str, str]]) -> str:
        tool_names = ", ".join(_tools.keys())
        
        # Formatuj ostatnie 4 wiadomości jako kontekst
        recent_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-4:]])

        prompt = f"""Your task is to choose a tool based on the user's last message in the context of the recent conversation.

        Available Tools:
        {self.tools_description}
        ---
        Recent Conversation History:
        {recent_history}
        ---

        Based on the LAST user message, which tool should be used? Respond with a single word: the name of the tool or "None".
        Tool:"""

        response = self.llm.generate_response([{'role': 'user', 'content': prompt}])
        response_lower = response.lower().strip().replace('"', '').replace("'", "").replace(".", "")

        for tool_name in _tools:
            if tool_name.lower() in response_lower:
                print(f"DEBUG: Router chose tool: {tool_name}")
                return tool_name

        print(f"DEBUG: Router chose no tool (AI response: '{response}')")
        return "None"

    def _get_tool_args(self, tool_name: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        target_tool = get_tool(tool_name)
        arg_spec = inspect.getfullargspec(target_tool)
        user_prompt = conversation_history[-1]['content']
        
        # Formatuj ostatnie 4 wiadomości jako kontekst dla ekstraktora
        recent_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-4:]])

        docstring = target_tool.__doc__.strip() if target_tool.__doc__ else "No description available."
        prompt = f"""Your task is to extract arguments for the tool '{tool_name}' from the user's request, using the conversation history for context.
        Tool's required arguments: {arg_spec.args}
        Tool's description: "{docstring}"

        Recent conversation history:
        ---
        {recent_history}
        ---

        Based on the last user message, extract the arguments. Respond ONLY with a valid JSON object. If no arguments are needed or can be found, respond with an empty JSON object {{}}.
        JSON:"""
        
        response = self.llm.generate_response([{'role': 'user', 'content': prompt}])
        try:
            cleaned_json = response[response.find('{'):response.rfind('}')+1]
            args = json.loads(cleaned_json)
            print(f"DEBUG: Router got arguments: {args}")
            return args
        except json.JSONDecodeError:
            print(f"ERROR: Failed to parse JSON arguments from response: {response}")
            return {}

    def process_turn(self, conversation_history: List[Dict[str, str]]) -> str:
        # Krok 1: Router wybiera narzędzie na podstawie historii
        chosen_tool_name = self._choose_tool(conversation_history)

        if chosen_tool_name != "None":
            tool_function = get_tool(chosen_tool_name)
            
            # Krok 2: Ekstraktor argumentów również używa historii
            if inspect.signature(tool_function).parameters:
                tool_args = self._get_tool_args(chosen_tool_name, conversation_history)
            else:
                tool_args = {}
                print(f"DEBUG: Tool '{chosen_tool_name}' requires no arguments.")

            # Krok 3: Wykonanie narzędzia
            try:
                result = tool_function(**tool_args)
                # Na razie wciąż zwracamy surowy wynik dla niezawodności
                # W przyszłości dodamy tu warstwę konwersacyjną
                return str(result)
            except Exception as e:
                return f"Error while executing tool {chosen_tool_name}: {e}"
        else:
            # Jeśli żadne narzędzie nie zostało wybrane, prowadź normalną rozmowę
            return self.llm.generate_response(conversation_history)
