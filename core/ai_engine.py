"""
Moduł zawierający główny silnik AI aplikacji.

Ten moduł implementuje klasę AIEngine, która zarządza wszystkimi operacjami
związanymi ze sztuczną inteligencją, w tym:
- Integracją z modelami LLM
- Obsługą konwersacji
- Systemem RAG (Retrieval-Augmented Generation)
"""

import json
import inspect
from typing import List, Dict, Any, Union, AsyncGenerator, cast, Callable, Optional
from pydantic import ValidationError

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from langchain.tools import Tool
from langchain_core.prompts import PromptTemplate as LangChainPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

from .llm_manager import LLMManager
from .module_system import load_modules, get_tool, _tools, get_tool_descriptions
from .tool_models import WeatherArgs, AddTaskArgs, ListTasksArgs, TaskIdArgs, MathArgs, BaseTool
from .rag_manager import RAGManager


class AIEngine:
    """Główny silnik AI aplikacji.
    
    Odpowiada za zarządzanie wszystkimi operacjami związanymi ze sztuczną inteligencją,
    w tym integracją z modelami LLM, obsługą konwersacji i systemem RAG.
    
    Attributes:
        config_manager: Menedżer konfiguracji aplikacji
        rag_manager: Menedżer systemu RAG
    """

    def __init__(self, config_manager) -> None:
        """Inicjalizuje silnik AI.
        
        Args:
            config_manager: Menedżer konfiguracji aplikacji
        """
        self.config_manager = config_manager
        
        # Inicjalizacja menedżera RAG
        self.rag_manager = RAGManager(config_manager)
        self.rag_manager.load_store()
        
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

    def _safe_call_tool(self, tool: Union[Callable, BaseTool], tool_args: Dict[str, Any]) -> Any:
        """
        Bezpiecznie wywołuje narzędzie, filtrując argumenty zgodnie z jego sygnaturą.
        
        Args:
            tool: Narzędzie do wywołania (funkcja lub instancja BaseTool)
            tool_args: Słownik argumentów do przekazania do narzędzia
            
        Returns:
            Any: Wynik wykonania narzędzia
            
        Raises:
            TypeError: Jeśli nie można wywołać narzędzia z podanymi argumentami
        """
        try:
            if isinstance(tool, BaseTool):
                # Dla narzędzi opartych na klasach, używamy metody execute
                return tool.execute(**tool_args)
            
            # Dla funkcji, sprawdzamy jej sygnaturę
            if not callable(tool):
                raise TypeError(f"Narzędzie nie jest wywoływalne: {type(tool)}")
                
            sig = inspect.signature(tool)
            valid_args = {}
            
            # Filtrujemy argumenty, zachowując tylko te, które są akceptowane przez funkcję
            for param_name, param in sig.parameters.items():
                if param_name in tool_args:
                    valid_args[param_name] = tool_args[param_name]
            
            return tool(**valid_args)
            
        except TypeError as e:
            print(f"ERROR: Błąd podczas wywoływania narzędzia: {str(e)}")
            raise

    def process_turn(self, conversation_history: List[Dict[str, str]]) -> str:
        """
        Przetwarza pojedynczą turę konwersacji, wybierając i wykonując odpowiednie narzędzie.
        
        Args:
            conversation_history: Lista słowników zawierających historię konwersacji
            
        Returns:
            str: Odpowiedź asystenta
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
                    return f"Błąd Walidacji Danych dla narzędzia '{chosen_tool_name}':\n{e}"
            else:
                tool_args = self._get_tool_args(chosen_tool_name, conversation_history)
            
            try:
                # Używamy nowej metody _safe_call_tool do bezpiecznego wywołania narzędzia
                tool_result = self._safe_call_tool(tool, tool_args)
                    
                final_response_prompt = f"""You are a helpful assistant. A tool has just been executed...
                Tool's result: "{tool_result}"
                Based on the tool's result, formulate a brief, natural, and helpful response to the user in Polish."""
                return self.llm.generate_response([{'role': 'user', 'content': final_response_prompt}])
            except Exception as e:
                return f"Error while executing tool {chosen_tool_name}: {e}"
        else:
            # Użyj głównego łańcucha LangChain dla odpowiedzi
            # Tworzymy czysty słownik z tylko wymaganymi kluczami
            chain_input = {
                'input': user_prompt,
                'history': self.memory.buffer,
                'tools': self.tools_description
            }
            return self.chain.predict(**chain_input)

    async def process_turn_stream(self, conversation_history: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Asynchroniczna wersja process_turn, która zwraca strumień odpowiedzi.
        
        Args:
            conversation_history: Lista słowników zawierających historię konwersacji
            
        Yields:
            str: Fragmenty odpowiedzi asystenta
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
                except ValidationError as e:
                    yield f"Błąd Walidacji Danych dla narzędzia '{chosen_tool_name}':\n{e}"
                    return
            else:
                tool_args = self._get_tool_args(chosen_tool_name, conversation_history)
            
            try:
                # Używamy nowej metody _safe_call_tool do bezpiecznego wywołania narzędzia
                tool_result = self._safe_call_tool(tool, tool_args)
                    
                final_response_prompt = f"""You are a helpful assistant. A tool has just been executed...
                Tool's result: "{tool_result}"
                Based on the tool's result, formulate a brief, natural, and helpful response to the user in Polish."""
                
                async for chunk in self.llm.generate_response_stream([{'role': 'user', 'content': final_response_prompt}]):
                    yield chunk
            except Exception as e:
                yield f"Error while executing tool {chosen_tool_name}: {e}"
        else:
            # Użyj głównego łańcucha LangChain dla odpowiedzi
            # Tworzymy czysty słownik z tylko wymaganymi kluczami
            chain_input = {
                'input': user_prompt,
                'history': self.memory.buffer,
                'tools': self.tools_description
            }
            
            # Dla wersji strumieniowej, używamy odpowiedniej metody z LLM
            async for chunk in self.llm.generate_response_stream([{'role': 'user', 'content': user_prompt}]):
                yield chunk

    async def get_rag_response_stream(self, query: str) -> AsyncGenerator[str, None]:
        """Generuje strumień odpowiedzi na podstawie zapytania i kontekstu z bazy wektorowej.
        
        Args:
            query: Zapytanie użytkownika
            
        Yields:
            str: Fragmenty odpowiedzi generowane przez model
            
        Raises:
            ValueError: Jeśli baza wektorowa nie istnieje
        """
        # Pobierz retriever
        retriever = self.rag_manager.get_retriever()
        if retriever is None:
            raise ValueError("Baza wektorowa nie istnieje. Najpierw dodaj dokumenty.")
        
        # Szablon promptu dla RAG
        template = """Odpowiedz na pytanie użytkownika na podstawie poniższego kontekstu.
        Jeśli nie znasz odpowiedzi lub kontekst nie zawiera odpowiednich informacji,
        powiedz to wprost. Nie wymyślaj informacji.

        Kontekst:
        {context}

        Pytanie: {input}

        Odpowiedź:"""
        
        prompt = LangChainPromptTemplate.from_template(template)
        
        # Tworzenie łańcucha RAG
        document_chain = create_stuff_documents_chain(
            llm=self.config_manager.llm,
            prompt=prompt,
            output_parser=StrOutputParser()
        )
        
        retrieval_chain = create_retrieval_chain(
            retriever=retriever,
            combine_docs_chain=document_chain
        )
        
        # Generowanie odpowiedzi
        async for chunk in retrieval_chain.astream({"input": query}):
            if "answer" in chunk:
                yield chunk["answer"]
