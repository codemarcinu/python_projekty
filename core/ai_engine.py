"""
Main AI engine that orchestrates all components of the AI Assistant.
Handles the core logic for processing user inputs and generating responses.
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
import re
import logging

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.agents import AgentExecutor, ZeroShotAgent
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
    
    def _setup_chains(self) -> None:
        """Set up LangChain chains and prompts."""
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
        )
        
        # Initialize vector store
        try:
            vector_store = FAISS.load_local(
                self.settings.rag.vector_db_path,
                embeddings
            )
        except RuntimeError:
            # Jeśli indeks nie istnieje, tworzymy pusty
            print("Indeks FAISS nie istnieje, tworzę pusty indeks...")
            # Tworzymy indeks z jednym pustym tekstem, aby uniknąć błędu
            vector_store = FAISS.from_texts(
                ["Initial empty document"],
                embeddings,
                metadatas=[{"source": "system"}]
            )
            vector_store.save_local(self.settings.rag.vector_db_path)
            print("Pusty indeks FAISS utworzony.")
        
        # Basic conversation chain
        self.conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm_manager.llm,
            retriever=vector_store.as_retriever(),
            memory=ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            ),
            verbose=True
        )
        
        # Custom prompt template
        self.prompt_template = PromptTemplate(
            input_variables=["chat_history", "question"],
            template="""You are a helpful AI assistant. Use the following conversation history to provide context for your response.

Chat History:
{chat_history}

Current Question: {question}

Please provide a helpful and accurate response:"""
        )
    
    def _setup_tools(self) -> None:
        """Set up tools for the agent."""
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
        
        # Create prompt template
        prefix = """You are an AI assistant with access to various tools. Use these tools when appropriate to help the user.

Available tools:
{tools}

Let's approach this step by step:
1. First, I'll analyze the user's request
2. Then, I'll decide if I need to use any tools
3. Finally, I'll provide a helpful response

Current conversation:
{chat_history}

User input: {input}

{agent_scratchpad}"""
        
        # Create agent
        self.agent = ZeroShotAgent(
            llm_chain=self.llm_manager.llm,
            tools=self.tools,
            prefix=prefix
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True
        )
    
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
        conversation: Conversation,
        message: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Process a user message and generate a response.
        
        Args:
            conversation: The current conversation
            message: The user's message
            system_prompt: Optional system prompt to guide the response
            
        Returns:
            Generated response
        """
        # Add user message to conversation
        conversation.add_message("user", message)
        
        try:
            if self.settings.llm.use_agent_mode:
                # Use agent mode with tools
                response = await self.agent_executor.arun(
                    input=message,
                    chat_history=conversation.get_context()
                )
            else:
                # Use standard generation
                response = await self.llm_manager.generate(
                    prompt=message,
                    system_prompt=system_prompt,
                    context=conversation.get_context()
                )
            
            # Add assistant response to conversation
            conversation.add_message("assistant", response)
            return response
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg)
            raise AIEngineError(error_msg)
    
    async def process_rag_query(
        self,
        query: str,
        conversation: Optional[Conversation] = None
    ) -> str:
        """
        Process a RAG query using the conversation chain.
        
        Args:
            query: The user's query
            conversation: Optional conversation for context
            
        Returns:
            Generated response with retrieved context
        """
        # Prepare chat history if conversation is provided
        chat_history = []
        if conversation:
            chat_history = conversation.get_context()
        
        # Process query through conversation chain
        response = await self.conversation_chain.arun(
            question=query,
            chat_history=chat_history
        )
        
        return response


# Create global AI engine instance
ai_engine = AIEngine()

def get_ai_engine() -> AIEngine:
    """Get the global AI engine instance."""
    return ai_engine
