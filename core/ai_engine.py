"""
Main AI engine that orchestrates all components of the AI Assistant.
Handles the core logic for processing user inputs and generating responses.
"""
from typing import Any, Dict, List, Optional, Union
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

from .config_manager import get_settings
from .conversation_handler import Conversation
from .llm_manager import get_llm_manager
from .exceptions import AIEngineError

# Configure logging
logger = logging.getLogger(__name__)

class AIEngine:
    """Main AI engine orchestrating all components."""
    
    def __init__(self):
        """Initialize the AI engine with required components."""
        self.settings = get_settings()
        self.llm_manager = get_llm_manager()
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
        """Set up RAG chains and vector store."""
        try:
            self._ensure_directories()
            # Initialize embeddings with new import
            embeddings = HuggingFaceEmbeddings(
                model_name=self.settings.rag.embedding_model,
                model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'}
            )
            # Initialize vector store with security flag
            try:
                vector_store = FAISS.load_local(
                    str(self.settings.rag.vector_db_path),
                    embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("Loaded existing FAISS vector store")
            except Exception as e:
                logger.warning(f"Could not load existing vector store: {e}")
                # Create empty vector store if loading fails
                vector_store = None
            self.vector_store = vector_store
            
            # Set up conversational retrieval chain only if vector store exists
            if self.vector_store:
                self.rag_chain = ConversationalRetrievalChain.from_llm(
                    llm=self.llm_manager.llm,
                    retriever=self.vector_store.as_retriever(),
                    verbose=True
                )
            else:
                self.rag_chain = None
                logger.warning("RAG chain not initialized - no vector store available")
        except Exception as e:
            logger.error(f"Error setting up chains: {e}")
            # Fallback setup
            self.vector_store = None
            self.rag_chain = None
    
    def _setup_tools(self) -> None:
        """Set up tools for the agent."""
        try:
            # Define available tools with improved descriptions
            self.tools = [
                Tool(
                    name="time",
                    func=self._time_tool,
                    description="Pobierz aktualną datę i czas. Używaj tego narzędzia gdy pytanie dotyczy aktualnej daty, dnia tygodnia, godziny lub czasu."
                ),
                Tool(
                    name="calculator",
                    func=self._calculator_tool,
                    description="Wykonaj obliczenia matematyczne. Input powinien być wyrażeniem matematycznym (np. '2+2')."
                ),
                Tool(
                    name="weather",
                    func=self._weather_tool,
                    description="Pobierz aktualną pogodę dla podanej lokalizacji. Input powinien być nazwą miasta."
                ),
                Tool(
                    name="search",
                    func=self._search_tool,
                    description="Wyszukaj informacje w internecie. Input powinien być zapytaniem wyszukiwania."
                )
            ]
            
            # Create modern React agent prompt with improved instructions
            prompt_template = """Jesteś asystentem AI z dostępem do różnych narzędzi.

WAŻNE ZASADY:
1. ZAWSZE używaj narzędzi, gdy pytanie dotyczy:
   - aktualnej daty, dnia tygodnia, godziny lub czasu (użyj narzędzia 'time')
   - obliczeń matematycznych (użyj narzędzia 'calculator')
   - pogody (użyj narzędzia 'weather')
   - wyszukiwania informacji (użyj narzędzia 'search')

2. NIE odpowiadaj na podstawie swojej wiedzy, jeśli istnieje odpowiednie narzędzie!
3. NIE zmyślaj dat, czasu ani innych informacji, które mogą być dostarczone przez narzędzia.
4. Jeśli nie jesteś pewien, czy użyć narzędzia - użyj go!

NARZĘDZIA:
---------
Masz dostęp do następujących narzędzi:

{tools}

Aby użyć narzędzia, użyj następującego formatu:

```
Thought: Czy muszę użyć narzędzia? Tak
Action: nazwa narzędzia do użycia, powinno być jednym z [{tool_names}]
Action Input: input do narzędzia
Observation: wynik działania narzędzia
```

Gdy masz odpowiedź do przekazania człowiekowi, lub gdy nie musisz używać narzędzia, MUSISZ użyć formatu:

```
Thought: Czy muszę użyć narzędzia? Nie
Final Answer: [twoja odpowiedź tutaj]
```

Zacznij!

Pytanie: {input}
Thought: {agent_scratchpad}"""

            prompt = PromptTemplate.from_template(prompt_template)
            
            # Create React agent using modern approach
            if self.llm_manager.llm:
                self.agent = create_react_agent(
                    llm=self.llm_manager.llm,
                    tools=self.tools,
                    prompt=prompt
                )
                
                # Create agent executor with improved error handling
                self.agent_executor = AgentExecutor(
                    agent=self.agent,
                    tools=self.tools,
                    verbose=True,
                    handle_parsing_errors=True,
                    max_iterations=3,
                    return_intermediate_steps=True
                )
                
                logger.info("Agent setup completed successfully")
            else:
                logger.warning("LLM not initialized, agent setup skipped")
                self.agent = None
                self.agent_executor = None
            
        except Exception as e:
            logger.error(f"Error setting up agent: {e}")
            # Fallback - disable agent functionality
            self.agent = None
            self.agent_executor = None
            self.tools = []
    
    def _search_tool(self, query: str) -> str:
        """Search tool implementation."""
        try:
            # Mock implementation - in real app would use actual search API
            return f"Wyniki wyszukiwania dla '{query}': Funkcja wyszukiwania jest w fazie rozwoju."
        except Exception as e:
            logger.error(f"Search tool error: {e}")
            return f"Błąd wyszukiwania: {str(e)}"
    
    def _calculator_tool(self, expression: str) -> str:
        """Calculator tool implementation."""
        try:
            # Safe calculation of basic operations
            allowed_chars = set('0123456789+-*/().,= ')
            if not all(c in allowed_chars for c in expression):
                return "Błąd: Niedozwolone znaki w wyrażeniu"
            
            result = eval(expression)
            return f"Wynik: {result}"
        except Exception as e:
            logger.error(f"Calculator tool error: {e}")
            return f"Błąd kalkulacji: {str(e)}"
    
    def _weather_tool(self, location: str) -> str:
        """Weather tool implementation."""
        try:
            # Mock weather data - in real app would use weather API
            weather_data = {
                "warszawa": "Słonecznie, 22°C",
                "kraków": "Pochmurnie, 18°C", 
                "gdańsk": "Deszczowo, 15°C"
            }
            
            location_lower = location.lower()
            if location_lower in weather_data:
                return f"Pogoda w {location}: {weather_data[location_lower]}"
            else:
                return f"Brak danych pogodowych dla {location}"
        except Exception as e:
            logger.error(f"Weather tool error: {e}")
            return f"Błąd pobierania pogody: {str(e)}"
    
    def _time_tool(self, input_text: str = "") -> str:
        """Time tool implementation."""
        try:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Time tool error: {e}")
            return f"Błąd pobierania czasu: {str(e)}"
    
    async def process_message(
        self, 
        message: str, 
        model: str = "gemma3:12b",
        use_rag: bool = True
    ) -> str:
        """
        Process a user message and generate a response.
        
        Args:
            message: User's message
            model: Model to use for generation
            use_rag: Whether to use RAG for response generation
            
        Returns:
            str: Generated response
        """
        try:
            # Initialize LLM if not already initialized
            if not self.llm_manager.llm:
                await self.llm_manager.initialize_llm()
            
            # Check if message requires agent tools
            time_keywords = ["jaki jest dzień", "jaka jest data", "która godzina", "jaki mamy dzień", "jaka jest godzina", "kiedy", "data", "godzina", "czas"]
            calc_keywords = ["oblicz", "policz", "ile to", "wynik", "dodaj", "odejmij", "pomnóż", "podziel"]
            weather_keywords = ["pogoda", "temperatura", "deszcz", "słońce", "śnieg"]
            search_keywords = ["wyszukaj", "znajdź", "szukaj", "informacje o"]
            
            all_keywords = time_keywords + calc_keywords + weather_keywords + search_keywords
            
            if any(keyword in message.lower() for keyword in all_keywords):
                try:
                    # Use agent executor for tool-based responses
                    result = await self.agent_executor.ainvoke({"input": message})
                    return result["output"]
                except Exception as e:
                    logger.error(f"Agent execution error: {e}")
                    # Fallback to direct LLM response
                    return await self._direct_llm_response(message)
            
            # Use RAG if enabled and available
            if use_rag and self.rag_chain:
                try:
                    return await self.process_rag_query(message)
                except Exception as e:
                    logger.error(f"RAG processing error: {e}")
                    # Fallback to direct LLM response
                    return await self._direct_llm_response(message)
            
            # Direct LLM response as fallback
            return await self._direct_llm_response(message)
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise AIEngineError(error_msg)
    
    async def _direct_llm_response(self, message: str) -> str:
        """Get direct response from LLM without tools."""
        try:
            response = await self.llm_manager.generate(message)
            return str(response) if response is not None else "Nie wygenerowano odpowiedzi"
        except Exception as e:
            logger.error(f"Direct LLM error: {e}")
            return "Przepraszam, nie mogę teraz odpowiedzieć."
    
    async def process_rag_query(self, query: str, chat_history: str = "") -> str:
        """Process a query using the RAG chain if available."""
        if not query:
            return "No query provided."
        if self.rag_chain is None:
            logger.warning("RAG chain is not initialized. Cannot process query.")
            return "RAG chain is not available. Please add documents or check vector store setup."
        try:
            response = await self.rag_chain.arun(
                question=query,
                chat_history=chat_history or ""
            )
            return str(response) if response is not None else "No response generated"
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            return f"Error processing RAG query: {e}"

    def get_agent_status(self) -> dict:
        """Get current agent status and available tools."""
        return {
            "agent_available": self.agent_executor is not None,
            "tools_count": len(self.tools) if self.tools else 0,
            "available_tools": [tool.name for tool in self.tools] if self.tools else [],
            "default_enabled": True
        }

# Create global AI engine instance
ai_engine = AIEngine()

def get_ai_engine() -> AIEngine:
    """Get the global AI engine instance."""
    return ai_engine
