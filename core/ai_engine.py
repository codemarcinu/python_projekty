"""
Moduł zawierający główny silnik AI odpowiedzialny za zarządzanie logiką agenta AI.

Ten moduł implementuje klasę AIEngine, która koordynuje działanie modelu językowego
z systemem wtyczek, umożliwiając agentowi wykonywanie zadań i odpowiadanie użytkownikowi.
"""

import json
import inspect
from typing import List, Dict, Any, Union, AsyncGenerator, cast, Callable
from pydantic import ValidationError

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from langchain.tools import Tool

from .llm_manager import LLMManager
from .module_system import load_modules, get_tool, _tools, get_tool_descriptions
from .tool_models import WeatherArgs, AddTaskArgs, ListTasksArgs, TaskIdArgs, MathArgs, BaseTool


class AIEngine:
    """
    Główny silnik AI, działający w oparciu o architekturę "Routera Narzędzi".
    Wykorzystuje LangChain do zarządzania konwersacją i routingiem narzędzi.
    """

    def __init__(self):
        load_modules("modules")
        self.tools_description = self._get_formatted_tools_description()
        self.tool_arg_models = {
            "get_current_weather": WeatherArgs,
            "add_task": AddTaskArgs,
            "list_tasks": ListTasksArgs,
            "complete_task": TaskIdArgs,
            "delete_task": TaskIdArgs,
            "add": MathArgs,
            "multiply": MathArgs,
        }
        
        # Inicjalizacja komponentów LangChain
        self.llm = LLMManager()
        self.memory = ConversationBufferMemory(
            memory_key="history",
            return_messages=True,
            output_key="output"
        )
        
        # Konwersja naszych narzędzi do formatu LangChain
        self.langchain_tools = self._create_langchain_tools()
        
        # Szablon promptu dla głównego łańcucha
        self.main_prompt = PromptTemplate(
            input_variables=["history", "input", "tools"],
            template="""Jesteś pomocnym asystentem AI. Masz dostęp do następujących narzędzi:

{tools}

Historia konwersacji:
{history}

Użytkownik: {input}
Asystent:"""
        )
        
        # Główny łańcuch LangChain
        self.chain = LLMChain(
            llm=self.llm.get_langchain_llm(),
            prompt=self.main_prompt,
            memory=self.memory,
            verbose=True
        )
        
        # Szablon promptu dla routera narzędzi
        self.router_prompt = PromptTemplate(
            input_variables=["history", "tools"],
            template="""Twoim zadaniem jest wybór odpowiedniego narzędzia na podstawie ostatniej wiadomości użytkownika.

Dostępne narzędzia:
{tools}

Historia konwersacji:
{history}

Na podstawie OSTATNIEJ wiadomości użytkownika, które narzędzie powinno być użyte? 
Odpowiedz jednym słowem: nazwą narzędzia lub "None".
Narzędzie:"""
        )
        
        # Łańcuch dla routera narzędzi
        self.router_chain = LLMChain(
            llm=self.llm.get_langchain_llm(),
            prompt=self.router_prompt,
            verbose=True
        )
        
        print("AI Engine (v2.0 with LangChain) has been initialized.")

    def _create_langchain_tools(self) -> List[Tool]:
        """
        Konwertuje nasze narzędzia do formatu LangChain Tool.
        
        Returns:
            List[Tool]: Lista narzędzi w formacie LangChain.
        """
        tools = []
        for name, tool in _tools.items():
            if isinstance(tool, BaseTool):
                # Dla klas dziedziczących po BaseTool
                tools.append(Tool(
                    name=tool.name,
                    description=tool.description,
                    func=tool.execute
                ))
            else:
                # Dla funkcji z dekoratorem @tool
                tools.append(Tool(
                    name=name,
                    description=tool.__doc__.strip() if tool.__doc__ else "No description available.",
                    func=tool
                ))
        return tools

    def _get_formatted_tools_description(self) -> str:
        """Tworzy opis narzędzi dla promptu routera."""
        descriptions = []
        for name, tool in _tools.items():
            if isinstance(tool, BaseTool):
                descriptions.append(f"- {tool.name}: {tool.description}")
            else:
                docstring = tool.__doc__.strip() if tool.__doc__ else "No description available."
                descriptions.append(f"- {name}: {docstring}")
        return "\n".join(descriptions)

    def _choose_tool(self, conversation_history: List[Dict[str, str]]) -> str:
        """Wybiera odpowiednie narzędzie na podstawie kontekstu konwersacji."""
        # Konwertuj historię do formatu LangChain
        langchain_history = "\n".join([
            f"{'Human' if msg['role'] == 'user' else 'AI'}: {msg['content']}"
            for msg in conversation_history[-4:]
        ])
        
        response = self.router_chain.predict(
            history=langchain_history,
            tools=self.tools_description
        )
        
        response_lower = response.lower().strip().replace('"', '').replace("'", "").replace(".", "")
        
        for tool_name in _tools:
            if tool_name.lower() in response_lower:
                print(f"DEBUG: Router chose tool: {tool_name}")
                return tool_name
        
        print(f"DEBUG: Router chose no tool (AI response: '{response}')")
        return "None"

    def _get_tool_args(self, tool_name: str, conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        """Ekstrahuje argumenty dla wybranego narzędzia z kontekstu konwersacji."""
        user_prompt = conversation_history[-1]['content']
        
        # Obsługa specjalnych przypadków dla zadań
        if tool_name in ["complete_task", "delete_task"] and any(word in user_prompt.lower() for word in ["wszystkie", "wszystko", "każde", "all"]):
            print("DEBUG: Wykryto polecenie masowe. Pobieram wszystkie ID zadań.")
            all_tasks_str = get_tool("list_tasks")()
            task_ids = [int(line.split(']')[0].split('[ID: ')[1]) for line in all_tasks_str.split('\n') if line.startswith('- [ID:')]
            if task_ids:
                return {"task_ids": task_ids}

        target_tool = get_tool(tool_name)
        if isinstance(target_tool, BaseTool):
            # Dla narzędzi opartych na klasach, przekazujemy query jako argument
            return {"query": user_prompt}
            
        arg_spec = inspect.getfullargspec(target_tool)
        recent_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-4:]])
        docstring = target_tool.__doc__.strip() if target_tool.__doc__ else "No description available."
        
        prompt = f"""Extract arguments for the tool '{tool_name}' from the user's request.
        Tool description: {docstring}
        Required arguments: {arg_spec.args}
        Recent conversation history:
        {recent_history}

        Respond ONLY with a valid JSON object containing the extracted arguments.
        Example format: {{"argument_name": "argument_value"}}
        Do not include any other text or explanation, just the JSON object.
        JSON:"""
        
        response = self.llm.generate_response([{'role': 'user', 'content': prompt}])
        try:
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx == -1 or end_idx == 0:
                raise json.JSONDecodeError("No JSON object found", response, 0)
            
            cleaned_json = response[start_idx:end_idx]
            args = json.loads(cleaned_json)
            print(f"DEBUG: Router got raw arguments: {args}")
            return args
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON arguments from response: {response}")
            print(f"ERROR details: {str(e)}")
            return {}

    def process_turn(self, conversation_history: List[Dict[str, str]]) -> str:
        """Przetwarza pojedynczą turę konwersacji, wybierając i wykonując odpowiednie narzędzie."""
        user_prompt = conversation_history[-1]['content']
        chosen_tool_name = self._choose_tool(conversation_history)

        if chosen_tool_name != "None":
            tool = get_tool(chosen_tool_name)
            model_class = self.tool_arg_models.get(chosen_tool_name)
            
            tool_args = {}
            if model_class and not isinstance(tool, BaseTool):
                extracted_args = self._get_tool_args(chosen_tool_name, conversation_history)
                try:
                    validated_args = model_class(**extracted_args)
                    tool_args = validated_args.model_dump()
                    print(f"DEBUG: Validated arguments: {tool_args}")
                except ValidationError as e:
                    return f"Błąd Walidacji Danych dla narzędzia '{chosen_tool_name}':\n{e}"
            else:
                tool_args = self._get_tool_args(chosen_tool_name, conversation_history)
            
            try:
                if isinstance(tool, BaseTool):
                    # Dla narzędzi opartych na klasach, używamy metody execute
                    tool_result = tool.execute(**tool_args)
                else:
                    # Dla funkcji z dekoratorem @tool, wywołujemy je bezpośrednio
                    tool_result = tool(**tool_args)
                    
                final_response_prompt = f"""You are a helpful assistant. A tool has just been executed...
                Tool's result: "{tool_result}"
                Based on the tool's result, formulate a brief, natural, and helpful response to the user in Polish."""
                return self.llm.generate_response([{'role': 'user', 'content': final_response_prompt}])
            except Exception as e:
                return f"Error while executing tool {chosen_tool_name}: {e}"
        else:
            # Użyj głównego łańcucha LangChain dla odpowiedzi
            return self.chain.predict(
                input=user_prompt,
                tools=self.tools_description
            )

    async def process_turn_stream(self, conversation_history: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Asynchroniczna wersja process_turn, która strumieniuje odpowiedź token po tokenie.
        
        Args:
            conversation_history (List[Dict[str, str]]): Historia konwersacji.
            
        Yields:
            str: Pojedynczy token odpowiedzi.
        """
        user_prompt = conversation_history[-1]['content']
        chosen_tool_name = self._choose_tool(conversation_history)

        if chosen_tool_name != "None":
            tool = get_tool(chosen_tool_name)
            model_class = self.tool_arg_models.get(chosen_tool_name)
            
            tool_args = {}
            if model_class and not isinstance(tool, BaseTool):
                extracted_args = self._get_tool_args(chosen_tool_name, conversation_history)
                try:
                    validated_args = model_class(**extracted_args)
                    tool_args = validated_args.model_dump()
                    print(f"DEBUG: Validated arguments: {tool_args}")
                except ValidationError as e:
                    error_msg = f"Błąd Walidacji Danych dla narzędzia '{chosen_tool_name}':\n{e}"
                    yield error_msg
                    return
            else:
                tool_args = self._get_tool_args(chosen_tool_name, conversation_history)
            
            try:
                # Wykonujemy narzędzie i pobieramy wynik
                if isinstance(tool, BaseTool):
                    # Dla narzędzi implementujących protokół BaseTool
                    tool_result = tool.execute(**tool_args)
                elif callable(tool):
                    # Dla funkcji z dekoratorem @tool
                    tool_result = tool(**tool_args)
                else:
                    raise TypeError(f"Narzędzie '{chosen_tool_name}' nie jest ani BaseTool, ani funkcją")
                    
                final_response_prompt = f"""You are a helpful assistant. A tool has just been executed...
                Tool's result: "{tool_result}"
                Based on the tool's result, formulate a brief, natural, and helpful response to the user in Polish."""
                
                # Strumieniujemy odpowiedź token po tokenie
                async for token in self.llm.generate_response_stream([{'role': 'user', 'content': final_response_prompt}]):
                    yield token
                    
            except Exception as e:
                error_msg = f"Error while executing tool {chosen_tool_name}: {e}"
                yield error_msg
        else:
            # Używamy strumieniowania dla głównego łańcucha LangChain
            response = await self.chain.ainvoke({
                "input": user_prompt,
                "tools": self.tools_description
            })
            yield response["output"]
