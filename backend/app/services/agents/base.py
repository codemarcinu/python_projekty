from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
import json
import logging
from pydantic import BaseModel, Field

from app.services.ollama.service import OllamaService
from app.services.ollama.exceptions import OllamaServiceError

logger = logging.getLogger(__name__)

class AgentState(BaseModel):
    """Base state for agent execution."""
    messages: List[Dict[str, str]] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class AgentResponse(BaseModel):
    """Base response model for agent actions."""
    content: str
    state: AgentState
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseAgent(ABC):
    """Base class for all AI agents."""
    
    def __init__(
        self,
        ollama_service: OllamaService,
        model_name: str,
        system_prompt: str,
        **kwargs
    ):
        """Initialize the agent."""
        self.ollama = ollama_service
        self.model_name = model_name
        self.system_prompt = system_prompt
        self.state = AgentState()
        self.tools: List[Any] = []
        self._setup_tools()
    
    def _setup_tools(self) -> None:
        """Set up agent tools. Override in subclasses."""
        pass
    
    @abstractmethod
    async def process(
        self,
        message: str,
        state: Optional[AgentState] = None,
        **kwargs
    ) -> AgentResponse:
        """Process a message and return a response."""
        pass
    
    async def _generate_response(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> str:
        """Generate a response using the LLM."""
        try:
            messages = []
            
            # Add system prompt
            messages.append({
                "role": "system",
                "content": self.system_prompt
            })
            
            # Add context if provided
            if context:
                messages.extend(context)
            
            # Add current prompt
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Generate response
            response = await self.ollama.generate_with_context(
                prompt=prompt,
                model_name=self.model_name,
                context=messages,
                **kwargs
            )
            
            return response
            
        except OllamaServiceError as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def _update_state(self, **kwargs) -> None:
        """Update agent state."""
        self.state.updated_at = datetime.now()
        for key, value in kwargs.items():
            if hasattr(self.state, key):
                setattr(self.state, key, value)
    
    def _add_message(self, role: str, content: str) -> None:
        """Add a message to the state."""
        self.state.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    async def reset(self) -> None:
        """Reset agent state."""
        self.state = AgentState()
    
    def get_state(self) -> AgentState:
        """Get current agent state."""
        return self.state
    
    def set_state(self, state: AgentState) -> None:
        """Set agent state."""
        self.state = state 