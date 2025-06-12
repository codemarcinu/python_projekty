import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import os

from langchain.chains import ConversationalRetrievalChain
from langchain_core.memory import BaseMemory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain_ollama import OllamaLLM

from app.core.config import get_settings
from app.services.conversation.service import ConversationService
from app.services.ai.interfaces import AIServiceInterface, RAGServiceInterface
from app.services.ai.exceptions import (
    AIServiceError, ModelNotFoundError, ProcessingError,
    RAGError, VectorStoreError, AgentError, ToolExecutionError
)

logger = logging.getLogger(__name__)

class AIService(AIServiceInterface):
    """Service for AI operations with dependency injection."""
    
    def __init__(
        self,
        conversation_service: ConversationService,
        settings: Optional[Dict[str, Any]] = None
    ):
        """Initialize the AI service with dependencies."""
        self.settings = settings or get_settings()
        self.conversation_service = conversation_service
        
        # Initialize components
        self._setup_llm()
        self._setup_rag()
        self._setup_agent()
    
    def _setup_llm(self) -> None:
        """Initialize the LLM component."""
        try:
            self.llm = OllamaLLM(model="gemma3:12b")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise ModelNotFoundError(f"Failed to initialize LLM: {e}")
    
    def _setup_rag(self) -> None:
        """Initialize RAG components."""
        try:
            self._ensure_directories()
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            try:
                self.vector_store = FAISS.load_local(
                    str(self.settings.rag.vector_db_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("Loaded existing FAISS vector store")
            except Exception as e:
                logger.warning(f"Could not load existing vector store: {e}")
                self.vector_store = None
            
            if self.vector_store:
                self.rag_chain = ConversationalRetrievalChain.from_llm(
                    llm=self.llm,
                    retriever=self.vector_store.as_retriever(),
                    verbose=True
                )
            else:
                logger.warning("Vector store not available, RAG chain not initialized")
                self.rag_chain = None
                
        except Exception as e:
            logger.error(f"Failed to initialize RAG: {e}")
            raise RAGError(f"Failed to initialize RAG: {e}")
    
    def _setup_agent(self) -> None:
        """Initialize the AI agent with tools."""
        try:
            # Load tools from modules
            self.tools = self._load_tools()
            
            if not self.tools:
                logger.warning("No tools found, agent not initialized")
                self.agent = None
                self.agent_executor = None
                return
            
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
                
                logger.info(f"Agent configured successfully with {len(self.tools)} tools")
            else:
                logger.warning("LLM not initialized, agent configuration skipped")
                self.agent = None
                self.agent_executor = None
                
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            raise AgentError(f"Failed to initialize agent: {e}")
    
    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        try:
            vector_db_path = Path(self.settings.rag.vector_db_path)
            vector_db_path.parent.mkdir(parents=True, exist_ok=True)
            uploads_path = Path("uploads")
            uploads_path.mkdir(exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directories: {e}")
            raise AIServiceError(f"Failed to create required directories: {e}")
    
    def _load_tools(self) -> List[Tool]:
        """Load tools from modules."""
        try:
            # TODO: Implement tool loading from modules
            return []
        except Exception as e:
            logger.error(f"Failed to load tools: {e}")
            raise ToolExecutionError(f"Failed to load tools: {e}")
    
    async def process_message(self, message: str, conversation_id: str) -> str:
        """Process a user message and return a response."""
        try:
            # Get conversation
            conversation = await self.conversation_service.get_conversation(conversation_id)
            if not conversation:
                raise ProcessingError(f"Conversation {conversation_id} not found")
            
            # Add user message
            await self.conversation_service.add_message(conversation_id, "user", message)
            
            # Process with agent if available
            if self.agent_executor is not None:
                try:
                    response = await self.agent_executor.ainvoke({"input": message})
                    await self.conversation_service.add_message(
                        conversation_id, "assistant", response["output"]
                    )
                    return response["output"]
                except Exception as e:
                    logger.error(f"Agent error: {e}")
                    # Fallback to direct LLM response
            
            # Fallback to direct LLM response
            response = self.llm.invoke(message)
            await self.conversation_service.add_message(conversation_id, "assistant", response)
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise ProcessingError(f"Error processing message: {e}")
    
    async def list_models(self) -> List[str]:
        """List available AI models."""
        try:
            # TODO: Implement model listing from Ollama
            return ["gemma3:12b"]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            raise ModelNotFoundError(f"Error listing models: {e}")
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and configuration."""
        return {
            "agent_initialized": self.agent is not None,
            "tools_count": len(self.tools) if hasattr(self, 'tools') else 0,
            "rag_available": self.rag_chain is not None,
            "vector_store_available": self.vector_store is not None
        } 