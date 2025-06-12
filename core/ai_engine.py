"""
Main AI engine that orchestrates all components of the AI Assistant.
Handles the core logic for processing user inputs and generating responses.
"""
from typing import Any, Dict, List, Optional, Union, Callable, Protocol, runtime_checkable
from datetime import datetime
import json
import re
import logging
import os
from pathlib import Path

from langchain.chains import ConversationalRetrievalChain
from langchain_core.memory import BaseMemory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.agents import AgentExecutor
from langchain.agents import create_react_agent
from langchain.tools import Tool
import torch
from langchain_ollama import OllamaLLM

from .config_manager import get_settings
from .conversation_handler import Conversation, get_conversation_manager
from .llm_manager import get_llm_manager
from .exceptions import AIEngineError
from .module_system import get_registered_tools, load_modules
from .tool_models import BaseTool

# Configure logging
logger = logging.getLogger(__name__)

# Type alias dla funkcji narzędzi
ToolFunc = Callable[..., str]

class AIEngine:
    """Main AI engine orchestrating all components."""
    
    def __init__(self):
        """Initialize the AI engine with required components."""
        self.settings = get_settings()
        self.llm_manager = get_llm_manager()
        self.conversation_manager = get_conversation_manager()
        
        # Load all modules from the modules directory
        try:
            modules_dir = os.path.join(os.path.dirname(__file__), '..', 'modules')
            load_modules(modules_dir)
            logger.info(f"Załadowano moduły z katalogu: {modules_dir}")
        except Exception as e:
            logger.error(f"Błąd podczas ładowania modułów: {e}", exc_info=True)
        
        self._setup_chains()
        self._setup_tools()
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        try:
            # Create vector DB directory if it doesn't exist
            vector_db_path = Path(self.settings.rag.vector_db_path)
            vector_db_path.parent.mkdir(parents=True, exist_ok=True)
            # Create uploads directory if it doesn't exist
            uploads_path = Path("uploads")
            uploads_path.mkdir(exist_ok=True)
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            raise AIEngineError(f"Failed to create required directories: {e}")
    
    def _setup_chains(self) -> None:
        """Konfiguruje łańcuchy LangChain."""
        try:
            # Initialize LLM
            self.llm = OllamaLLM(model="gemma3:12b")
            self._ensure_directories()
            # Initialize embeddings with new import
            self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            # Initialize vector store with security flag
            try:
                vector_store = FAISS.load_local(
                    str(self.settings.rag.vector_db_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("Loaded existing FAISS vector store")
            except Exception as e:
                logger.warning(f"Could not load existing vector store: {e}")
                # Create empty vector store if loading fails
                vector_store = None
            self.vector_store = vector_store
            
            # Setup RAG chain if vector store is available
            if self.vector_store:
                self.rag_chain = ConversationalRetrievalChain.from_llm(
                    llm=self.llm,
                    retriever=self.vector_store.as_retriever(),
                    verbose=True
                )
            else:
                logging.warning("Vector store not available, RAG chain not initialized")
        except Exception as e:
            logging.error(f"Error setting up chains: {e}")
            # Fallback setup
            self.vector_store = None
            self.rag_chain = None
    
    def _setup_tools(self) -> None:
        """DYNAMICZNIE ładuje narzędzia z systemu modułów i konfiguruje agenta."""
        try:
            # Pobierz wszystkie funkcje zarejestrowane dekoratorem @tool
            registered_tools = get_registered_tools()
            
            self.tools = []
            for name, tool in registered_tools.items():
                # Użyj docstring funkcji jako opisu dla narzędzia
                description = tool.__doc__ or f"Narzędzie o nazwie {name}"
                
                # Obsługa różnych typów narzędzi
                if hasattr(tool, 'execute') and callable(getattr(tool, 'execute')):
                    # Dla obiektów z metodą execute (BaseTool)
                    execute_func: ToolFunc = tool.execute
                    tool_instance = Tool(
                        name=name,
                        func=execute_func,  # Używamy metody execute
                        description=description.strip()
                    )
                else:
                    # Dla zwykłych funkcji używamy ich bezpośrednio
                    func: ToolFunc = tool  # type: ignore
                    tool_instance = Tool(
                        name=name,
                        func=func,  # Funkcja jest już odpowiedniego typu
                        description=description.strip()
                    )
                
                self.tools.append(tool_instance)
                logger.info(f"Załadowano narzędzie: '{name}'")

            if not self.tools:
                logger.warning("Nie znaleziono żadnych zarejestrowanych narzędzi.")
                self.agent = None
                self.agent_executor = None
                return

            # Ten szablon promptu jest teraz jeszcze ważniejszy!
            prompt_template = """Jesteś asystentem AI z dostępem do różnych narzędzi.

WAŻNE ZASADY:
1. ZAWSZE analizuj, czy pytanie użytkownika pasuje do opisu jednego z dostępnych narzędzi.
2. Jeśli pytanie dotyczy informacji, którą może dostarczyć narzędzie (np. aktualna data, obliczenia), ZAWSZE użyj tego narzędzia.
3. NIE odpowiadaj na podstawie swojej wiedzy, jeśli istnieje dedykowane narzędzie! Musisz go użyć.
4. NIE zmyślaj dat, czasu ani innych informacji, które mogą być dostarczone przez narzędzia.

NARZĘDZIA:
---------
Masz dostęp do następujących narzędzi:

{tools}

Aby użyć narzędzia, użyj następującego formatu:

```
Thought: Czy muszę użyć narzędzia? Tak. Pytanie dotyczy [krótkie uzasadnienie], więc użyję narzędzia `[nazwa_narzędzia]`.
Action: nazwa narzędzia do użycia, powinno być jednym z [{tool_names}]
Action Input: input do narzędzia (może być pusty, jeśli nie jest wymagany)
Observation: wynik działania narzędzia
```

Gdy masz odpowiedź do przekazania człowiekowi, lub gdy nie musisz używać narzędzia, MUSISZ użyć formatu:

```
Thought: Czy muszę użyć narzędzia? Nie.
Final Answer: [twoja odpowiedź tutaj]
```

Zacznij!

Pytanie: {input}
Thought: {agent_scratchpad}"""

            prompt = PromptTemplate.from_template(prompt_template)
            
            # Tworzenie agenta pozostaje bez zmian
            if self.llm:
                self.agent = create_react_agent(
                    llm=self.llm,
                    tools=self.tools,
                    prompt=prompt
                )
                
                self.agent_executor = AgentExecutor(
                    agent=self.agent,
                    tools=self.tools,
                    verbose=True,
                    handle_parsing_errors="Zauważyłem błąd parsowania. Spróbuję jeszcze raz, analizując problem krok po kroku.",
                    max_iterations=5,
                    return_intermediate_steps=True
                )
                
                logger.info(f"Konfiguracja agenta zakończona pomyślnie. Załadowano {len(self.tools)} narzędzi.")
            else:
                logger.warning("LLM nie został zainicjowany, konfiguracja agenta pominięta.")
                self.agent = None
                self.agent_executor = None
            
        except Exception as e:
            logger.error(f"Krytyczny błąd podczas konfigurowania agenta: {e}", exc_info=True)
            self.agent = None
            self.agent_executor = None
            self.tools = []
    
    async def process_message(self, message: str, conversation_id: str) -> str:
        """Przetwarza wiadomość użytkownika i zwraca odpowiedź."""
        try:
            # Get conversation history
            conversation = self.conversation_manager.get_conversation(conversation_id)
            if not conversation:
                return "Nie znaleziono konwersacji."
            
            # Add user message to history
            conversation.add_message("user", message)
            
            # Process with agent if available
            if self.agent_executor is not None:
                try:
                    response = await self.agent_executor.ainvoke({"input": message})
                    conversation.add_message("assistant", response["output"])
                    return response["output"]
                except Exception as e:
                    logging.error(f"Agent error: {e}")
                    # Fallback to direct LLM response
            response = self._direct_llm_response(message)
            conversation.add_message("assistant", response)
            return response

        except Exception as e:
            logging.error(f"Error processing message: {e}")
            return "Przepraszam, wystąpił błąd podczas przetwarzania wiadomości."
    
    def generate(self, message: str) -> str:
        """Generuje bezpośrednią odpowiedź LLM bez użycia narzędzi."""
        try:
            response = self.llm.invoke(message)
            return response
        except Exception as e:
            logging.error(f"Error generating response: {e}")
            return f"Error generating response: {e}"
    
    def _direct_llm_response(self, message: str) -> str:
        """Generuje bezpośrednią odpowiedź LLM bez użycia narzędzi."""
        try:
            response = self.llm.invoke(message)
            return response
        except Exception as e:
            logging.error(f"Error generating direct response: {e}")
            return f"Error generating response: {e}"
    
    async def process_rag_query(self, query: str, chat_history: str = "") -> str:
        """
        Przetwarza zapytanie używając RAG.
        
        Args:
            query: Zapytanie użytkownika
            chat_history: Historia konwersacji
            
        Returns:
            str: Odpowiedź wygenerowana przez RAG
        """
        if not self.rag_chain:
            return "Przepraszam, system RAG nie jest dostępny."
        
        try:
            response = await self.rag_chain.ainvoke({
                "question": query,
                "chat_history": chat_history
            })
            return response["answer"]
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return "Przepraszam, wystąpił błąd podczas przetwarzania zapytania."
    
    def get_agent_status(self) -> dict:
        """
        Zwraca status agenta i dostępnych narzędzi.
        
        Returns:
            dict: Status agenta
        """
        return {
            "tools_loaded": len(self.tools) if hasattr(self, 'tools') else 0,
            "agent_configured": self.agent is not None,
            "rag_available": self.rag_chain is not None,
            "llm_initialized": self.llm is not None
        }

def get_ai_engine() -> AIEngine:
    """
    Zwraca instancję AIEngine (singleton).
    
    Returns:
        AIEngine: Instancja silnika AI
    """
    return AIEngine()
