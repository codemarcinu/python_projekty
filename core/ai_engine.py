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
from langchain.memory import ConversationBufferMemory
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
            # Set up conversational memory
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            # Set up conversational retrieval chain only if vector store exists
            if self.vector_store:
                self.rag_chain = ConversationalRetrievalChain.from_llm(
                    llm=self.llm_manager.llm,
                    retriever=self.vector_store.as_retriever(),
                    memory=self.memory,
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
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
    
    def _setup_tools(self) -> None:
        """Set up tools for the agent."""
        try:
            # Define available tools
            self.tools = [
                Tool(
                    name="search",
                    func=self._search_tool,
                    description="Search for information on the internet"
                ),
                Tool(
                    name="calculator",
                    func=self._calculator_tool,
                    description="Perform mathematical calculations"
                ),
                Tool(
                    name="weather",
                    func=self._weather_tool,
                    description="Get current weather information"
                ),
                Tool(
                    name="time",
                    func=self._time_tool,
                    description="Get current time and date"
                )
            ]
            
            # Create modern React agent prompt
            prompt_template = """You are an AI assistant with access to various tools.
Use these tools when appropriate to help answer questions.

TOOLS:
------
You have access to the following tools:

{tools}

To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

            prompt = PromptTemplate.from_template(prompt_template)
            
            # Create React agent using modern approach
            self.agent = create_react_agent(
                llm=self.llm_manager.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # Create agent executor
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=3
            )
            
            logger.info("Agent setup completed successfully")
            
        except Exception as e:
            logger.error(f"Error setting up agent: {e}")
            # Fallback - disable agent functionality
            self.agent = None
            self.agent_executor = None
            self.tools = []
    
    async def _search_tool(self, query: str) -> str:
        """Search tool implementation."""
        # TODO: Implement actual search functionality
        return f"Search results for: {query}"
    
    async def _calculator_tool(self, expression: str) -> str:
        """Calculator tool implementation."""
        try:
            result = eval(expression)
            return f"Result: {result}"
        except Exception as e:
            return f"Error calculating: {str(e)}"
    
    async def _weather_tool(self, location: str) -> str:
        """Weather tool implementation."""
        # TODO: Implement actual weather API integration
        return f"Weather information for: {location}"
    
    async def _time_tool(self, _: Any = None) -> str:
        """Time tool implementation."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    async def process_message(
        self, 
        message: str, 
        conversation_id: str = None,
        use_agent: bool = False
    ) -> str:
        """
        Process user message with optional agent capabilities.
        
        Args:
            message: User message
            conversation_id: Optional conversation ID
            use_agent: Whether to use agent tools
            
        Returns:
            AI response
        """
        try:
            if message is None:
                logger.error("Message argument is None in process_message.")
                return "No message provided."
            if use_agent and self.agent_executor:
                # Use agent with tools
                response = await self.agent_executor.ainvoke({
                    "input": message
                })
                output = response.get("output")
                return str(output) if output is not None else "No response generated"
            else:
                # Direct LLM response
                if message is None:
                    return "No message provided."
                response = await self.llm_manager.generate(str(message))
                return str(response) if response is not None else "No response generated"
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"Przepraszam, wystąpił błąd: {str(e)}"
    
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


# Create global AI engine instance
ai_engine = AIEngine()

def get_ai_engine() -> AIEngine:
    """Get the global AI engine instance."""
    return ai_engine
