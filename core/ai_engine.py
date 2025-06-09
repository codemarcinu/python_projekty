"""
Moduł zawierający główny silnik AI odpowiedzialny za zarządzanie logiką agenta AI.

Ten moduł implementuje klasę AIEngine, która koordynuje działanie modelu językowego
z systemem wtyczek, umożliwiając agentowi wykonywanie zadań i odpowiadanie użytkownikowi.
"""

import json
import inspect
from pydantic import ValidationError
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
        # Mapa modeli argumentów dla narzędzi
        self.tool_arg_models = {
            "get_current_weather": WeatherArgs,
            "add_task": AddTaskArgs,
            "list_tasks": ListTasksArgs,
            "complete_task": TaskIdArgs,
            "delete_task": TaskIdArgs,
            "add": MathArgs,
            "multiply": MathArgs,
        }
        print("AI Engine (Router - English Prompts) has been initialized.")

    def _get_formatted_tools_description(self) -> str:
        """Tworzy opis narzędzi dla promptu routera."""
        descriptions = []
        for name, func in _tools.items():
            docstring = func.__doc__.strip() if func.__doc__ else "No description available."
            descriptions.append(f"- {name}: {docstring}")
        return "\n".join(descriptions)

    def _choose_tool(self, user_prompt: str) -> str:
        tool_names = ", ".join(_tools.keys())
        prompt = f"""Your task is to choose a tool. Based on the user's request, which of the following tools is the most appropriate: [{tool_names}, None]?

        User request: "{user_prompt}"

        Respond with a single word: the name of the tool or "None".
        Tool:"""

        response = self.llm.generate_response([{'role': 'user', 'content': prompt}])
        response_lower = response.lower().strip().replace('"', '').replace("'", "").replace(".", "")

        for tool_name in _tools:
            if tool_name.lower() in response_lower:
                print(f"DEBUG: Router chose tool: {tool_name}")
                return tool_name

        print(f"DEBUG: Router chose no tool (AI response: '{response}')")
        return "None"

    def _get_tool_args(self, tool_name: str, user_prompt: str) -> Dict[str, Any]:
        """Etap 2a: Wydobycie argumentów dla wybranego narzędzia."""
        target_tool = get_tool(tool_name)
        arg_spec = inspect.getfullargspec(target_tool)
        
        prompt = f"""Your task is to extract arguments for the tool '{tool_name}' from the user's request.
        The tool's required arguments are: {arg_spec.args}.
        The tool's description is: "{target_tool.__doc__.strip() if target_tool.__doc__ else 'No description available.'}"

        User's request: "{user_prompt}"

        Respond ONLY with a valid JSON object containing the arguments. If no arguments are needed, respond with an empty JSON object {{}}.
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
        """Główna metoda przetwarzająca turę rozmowy."""
        user_prompt = conversation_history[-1]['content']
        
        # ETAP 1: ROUTING
        chosen_tool_name = self._choose_tool(user_prompt)

        # ETAP 2: WYKONANIE LUB ROZMOWA
        if chosen_tool_name != "None":
            tool_function = get_tool(chosen_tool_name)
            model_class = self.tool_arg_models.get(chosen_tool_name)

            tool_args = {}
            if model_class:  # Jeśli narzędzie ma zdefiniowany model argumentów
                extracted_args = self._get_tool_args(chosen_tool_name, user_prompt)
                try:
                    # Walidacja za pomocą Pydantic
                    validated_args = model_class(**extracted_args)
                    tool_args = validated_args.model_dump()
                except ValidationError as e:
                    return f"Błąd walidacji argumentów dla narzędzia '{chosen_tool_name}':\n{e}"

            try:
                result = tool_function(**tool_args)
                return str(result)
            except Exception as e:
                return f"Błąd podczas wykonywania narzędzia {chosen_tool_name}: {e}"
        else:
            # Jeśli żadne narzędzie nie zostało wybrane, prowadź normalną rozmowę
            return self.llm.generate_response(conversation_history)
