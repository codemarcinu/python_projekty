"""
Main AI engine that orchestrates all components of the AI Assistant.
Handles the core logic for processing user inputs and generating responses.
"""
from typing import Any, Dict, List, Optional

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
import torch

from .config_manager import get_settings
from .conversation_handler import Conversation
from .llm_manager import get_llm_manager


class AIEngine:
    """Main AI engine orchestrating all components."""
    
    def __init__(self):
        """Initialize the AI engine with required components."""
        self.settings = get_settings()
        self.llm_manager = get_llm_manager()
        self._setup_chains()
    
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
        
        # Get conversation context
        context = conversation.get_context()
        
        # Generate response
        response = await self.llm_manager.generate(
            prompt=message,
            system_prompt=system_prompt,
            context=context
        )
        
        # Add assistant response to conversation
        conversation.add_message("assistant", response)
        
        return response
    
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
