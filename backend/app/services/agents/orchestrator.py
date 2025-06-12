from typing import List, Dict, Any, Optional, Type
import logging
from datetime import datetime
from pydantic import BaseModel, Field

from app.services.agents.base import BaseAgent, AgentState, AgentResponse
from app.services.agents.specialized import ChatAgent, ResearchAgent, CodingAgent
from app.services.ollama.service import OllamaService
from app.core.config import settings

logger = logging.getLogger(__name__)

class AgentConfig(BaseModel):
    """Configuration for an agent."""
    type: str
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class OrchestratorState(BaseModel):
    """State for the agent orchestrator."""
    current_agent: Optional[str] = None
    agent_states: Dict[str, AgentState] = Field(default_factory=dict)
    workflow_history: List[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class AgentOrchestrator:
    """Orchestrator for managing multiple AI agents."""
    
    def __init__(
        self,
        ollama_service: OllamaService,
        configs: Optional[List[AgentConfig]] = None
    ):
        """Initialize the orchestrator."""
        self.ollama = ollama_service
        self.agents: Dict[str, BaseAgent] = {}
        self.state = OrchestratorState()
        
        # Default configurations
        default_configs = [
            AgentConfig(type="chat", model_name=settings.DEFAULT_CHAT_MODEL),
            AgentConfig(type="research", model_name=settings.DEFAULT_CHAT_MODEL),
            AgentConfig(type="code", model_name=settings.DEFAULT_CODE_MODEL)
        ]
        
        # Initialize agents
        for config in configs or default_configs:
            self._initialize_agent(config)
    
    def _initialize_agent(self, config: AgentConfig) -> None:
        """Initialize an agent based on configuration."""
        agent_class = self._get_agent_class(config.type)
        if not agent_class:
            logger.warning(f"Unknown agent type: {config.type}")
            return
        
        agent = agent_class(
            ollama_service=self.ollama,
            model_name=config.model_name,
            system_prompt=config.system_prompt,
            **config.metadata
        )
        
        self.agents[config.type] = agent
        self.state.agent_states[config.type] = agent.get_state()
    
    def _get_agent_class(self, agent_type: str) -> Optional[Type[BaseAgent]]:
        """Get agent class based on type."""
        agent_map = {
            "chat": ChatAgent,
            "research": ResearchAgent,
            "code": CodingAgent
        }
        return agent_map.get(agent_type)
    
    async def process(
        self,
        message: str,
        agent_type: Optional[str] = None,
        **kwargs
    ) -> AgentResponse:
        """Process a message using the appropriate agent."""
        try:
            # Determine which agent to use
            if agent_type:
                if agent_type not in self.agents:
                    raise ValueError(f"Unknown agent type: {agent_type}")
                target_agent = self.agents[agent_type]
            else:
                # TODO: Implement agent selection logic
                target_agent = self.agents["chat"]
            
            # Update orchestrator state
            self.state.current_agent = target_agent.__class__.__name__
            self.state.updated_at = datetime.now()
            
            # Get agent state
            agent_state = self.state.agent_states.get(target_agent.__class__.__name__)
            
            # Process message
            response = await target_agent.process(
                message=message,
                state=agent_state,
                **kwargs
            )
            
            # Update agent state
            self.state.agent_states[target_agent.__class__.__name__] = response.state
            
            # Add to workflow history
            self.state.workflow_history.append({
                "timestamp": datetime.now().isoformat(),
                "agent": target_agent.__class__.__name__,
                "message": message,
                "response": response.content,
                "metadata": response.metadata
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise
    
    async def switch_agent(self, agent_type: str) -> None:
        """Switch to a different agent."""
        if agent_type not in self.agents:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        self.state.current_agent = agent_type
        self.state.updated_at = datetime.now()
    
    async def reset(self, agent_type: Optional[str] = None) -> None:
        """Reset agent state(s)."""
        if agent_type:
            if agent_type not in self.agents:
                raise ValueError(f"Unknown agent type: {agent_type}")
            await self.agents[agent_type].reset()
            self.state.agent_states[agent_type] = self.agents[agent_type].get_state()
        else:
            for agent in self.agents.values():
                await agent.reset()
                self.state.agent_states[agent.__class__.__name__] = agent.get_state()
        
        self.state.workflow_history = []
        self.state.updated_at = datetime.now()
    
    def get_state(self) -> OrchestratorState:
        """Get current orchestrator state."""
        return self.state
    
    def get_agent_state(self, agent_type: str) -> Optional[AgentState]:
        """Get state for a specific agent."""
        if agent_type not in self.agents:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return self.state.agent_states.get(agent_type)
    
    def get_workflow_history(self) -> List[Dict[str, Any]]:
        """Get workflow history."""
        return self.state.workflow_history 