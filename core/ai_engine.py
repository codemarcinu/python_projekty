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
        # NOWA MAPA MODELI DO WALIDACJI
        self.tool_arg_models = {
            "get_current_weather": WeatherArgs,
            "add_task": AddTaskArgs,
            "list_tasks": ListTasksArgs,
            "complete_task": TaskIdArgs,
            "delete_task": TaskIdArgs,
            "add": MathArgs,
            "multiply": MathArgs,
        }
        self.llm = LLMManager()
        print("AI Engine (v1.1 with Pydantic Validation) has been initialized.")

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
        # --- NOWA, ULEPSZONA LOGIKA ---
        user_prompt = conversation_history[-1]['content']
        # Sprawdzanie słów kluczowych dla operacji masowych
        if tool_name in ["complete_task", "delete_task"] and any(word in user_prompt.lower() for word in ["wszystkie", "wszystko", "każde", "all"]):
            print("DEBUG: Wykryto polecenie masowe. Pobieram wszystkie ID zadań.")
            all_tasks_str = get_tool("list_tasks")()
            # Prosta metoda na wyciągnięcie ID z wyniku list_tasks
            task_ids = [int(line.split(']')[0].split('[ID: ')[1]) for line in all_tasks_str.split('\n') if line.startswith('- [ID:')]
            if task_ids:
                return {"task_ids": task_ids}

        # Standardowa logika, jeśli nie wykryto polecenia masowego
        target_tool = get_tool(tool_name)
        arg_spec = inspect.getfullargspec(target_tool)
        recent_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-4:]])
        docstring = target_tool.__doc__.strip() if target_tool.__doc__ else "No description available."
        prompt = f"""Your task is to extract arguments for the tool '{tool_name}' from the user's request...
        JSON:""" # Skrócony dla czytelności
        response = self.llm.generate_response([{'role': 'user', 'content': prompt}])
        try:
            cleaned_json = response[response.find('{'):response.rfind('}')+1]
            args = json.loads(cleaned_json)
            print(f"DEBUG: Router got raw arguments: {args}")
            return args
        except json.JSONDecodeError:
            print(f"ERROR: Failed to parse JSON arguments from response: {response}")
            return {}

    def process_turn(self, conversation_history: List[Dict[str, str]]) -> str:
        user_prompt = conversation_history[-1]['content']
        chosen_tool_name = self._choose_tool(conversation_history)

        if chosen_tool_name != "None":
            tool_function = get_tool(chosen_tool_name)
            model_class = self.tool_arg_models.get(chosen_tool_name)
            
            tool_args = {}
            if model_class:
                extracted_args = self._get_tool_args(chosen_tool_name, conversation_history)
                try:
                    # NOWA LOGIKA WALIDACJI
                    validated_args = model_class(**extracted_args)
                    tool_args = validated_args.model_dump()
                    print(f"DEBUG: Validated arguments: {tool_args}")
                except ValidationError as e:
                    return f"Błąd Walidacji Danych dla narzędzia '{chosen_tool_name}':\n{e}"
            
            try:
                tool_result = tool_function(**tool_args)
                final_response_prompt = f"""You are a helpful assistant. A tool has just been executed...
                Tool's result: "{tool_result}"
                Based on the tool's result, formulate a brief, natural, and helpful response to the user in Polish."""
                return self.llm.generate_response([{'role': 'user', 'content': final_response_prompt}])
            except Exception as e:
                return f"Error while executing tool {chosen_tool_name}: {e}"
        else:
            return self.llm.generate_response(conversation_history)
