"""
Base Agent class for the multi-agent system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum
import uuid
import asyncio
import logging
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    """Agent roles in the system"""
    MANAGER = "manager"
    BING_SEARCH = "bing_search"
    AI_SEARCH = "ai_search"
    EVALUATOR = "evaluator"


class AgentStatus(str, Enum):
    """Agent status states"""
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class MessageType(str, Enum):
    """Message types in agent communication"""
    QUERY = "query"
    RESPONSE = "response"
    ERROR = "error"
    STATUS = "status"
    COMMAND = "command"


@dataclass
class AgentMetrics:
    """Metrics for agent performance tracking"""
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    processing_time_ms: Optional[float] = None
    tokens_used: int = 0
    api_calls_made: int = 0
    errors_count: int = 0
    retry_count: int = 0
    
    def calculate_processing_time(self):
        """Calculate processing time in milliseconds"""
        if self.end_time:
            delta = self.end_time - self.start_time
            self.processing_time_ms = delta.total_seconds() * 1000
            return self.processing_time_ms
        return None


class AgentMessage(BaseModel):
    """Message structure for inter-agent communication"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: AgentRole
    receiver: Optional[AgentRole] = None
    message_type: MessageType
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    parent_message_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    """Standard response structure from agents"""
    agent_id: str
    agent_role: AgentRole
    status: AgentStatus
    content: Optional[Union[str, Dict[str, Any]]] = None
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)
    processing_time_ms: Optional[float] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BaseAgent(ABC):
    """Abstract base class for all agents in the system"""
    
    def __init__(
        self,
        role: AgentRole,
        name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base agent
        
        Args:
            role: The role of this agent
            name: Optional custom name for the agent
            config: Optional configuration dictionary
        """
        self.id = str(uuid.uuid4())
        self.role = role
        self.name = name or f"{role.value}_agent_{self.id[:8]}"
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.metrics = AgentMetrics()
        self.message_history: List[AgentMessage] = []
        self.current_task_id: Optional[str] = None
        
        # Performance tracking
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        
        logger.info(f"Initialized {self.name} with role {role.value}")
    
    @abstractmethod
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Process a query and return a response
        
        Args:
            query: The input query to process
            context: Optional context dictionary
            
        Returns:
            AgentResponse with the processing results
        """
        pass
    
    @abstractmethod
    async def validate_input(self, query: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate input before processing
        
        Args:
            query: The input query
            context: Optional context
            
        Returns:
            True if input is valid, False otherwise
        """
        pass
    
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Execute agent processing with error handling and metrics
        
        Args:
            query: The input query
            context: Optional context dictionary
            
        Returns:
            AgentResponse with results or error information
        """
        self._total_requests += 1
        self.status = AgentStatus.PROCESSING
        self.metrics = AgentMetrics()
        self.current_task_id = str(uuid.uuid4())
        
        try:
            # Validate input
            if not await self.validate_input(query, context):
                raise ValueError("Invalid input provided to agent")
            
            # Log incoming request
            logger.info(f"{self.name} processing query: {query[:100]}...")
            
            # Process the query
            response = await self.process(query, context)
            
            # Update metrics
            self.metrics.end_time = datetime.utcnow()
            processing_time = self.metrics.calculate_processing_time()
            response.processing_time_ms = processing_time
            
            # Update status
            self.status = AgentStatus.COMPLETED
            self._successful_requests += 1
            
            # Log success
            logger.info(f"{self.name} completed processing in {processing_time:.2f}ms")
            
            return response
            
        except asyncio.TimeoutError:
            self.status = AgentStatus.TIMEOUT
            self._failed_requests += 1
            logger.error(f"{self.name} timed out processing query")
            return self._create_error_response("Processing timed out", AgentStatus.TIMEOUT)
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self._failed_requests += 1
            logger.error(f"{self.name} failed with error: {str(e)}", exc_info=True)
            return self._create_error_response(str(e), AgentStatus.FAILED)
        
        finally:
            self.current_task_id = None
    
    def _create_error_response(self, error_message: str, status: AgentStatus) -> AgentResponse:
        """Create an error response"""
        return AgentResponse(
            agent_id=self.id,
            agent_role=self.role,
            status=status,
            error=error_message,
            processing_time_ms=self.metrics.calculate_processing_time() if self.metrics.end_time else None
        )
    
    async def send_message(self, receiver: AgentRole, message_type: MessageType, content: Dict[str, Any]) -> AgentMessage:
        """
        Send a message to another agent
        
        Args:
            receiver: The receiving agent's role
            message_type: Type of message
            content: Message content
            
        Returns:
            The sent message
        """
        message = AgentMessage(
            sender=self.role,
            receiver=receiver,
            message_type=message_type,
            content=content
        )
        self.message_history.append(message)
        logger.debug(f"{self.name} sent message to {receiver.value}: {message.id}")
        return message
    
    async def receive_message(self, message: AgentMessage) -> None:
        """
        Receive and process a message from another agent
        
        Args:
            message: The incoming message
        """
        self.message_history.append(message)
        logger.debug(f"{self.name} received message from {message.sender.value}: {message.id}")
        
        # Process based on message type
        if message.message_type == MessageType.COMMAND:
            await self._handle_command(message)
        elif message.message_type == MessageType.QUERY:
            await self._handle_query(message)
    
    async def _handle_command(self, message: AgentMessage) -> None:
        """Handle command messages"""
        command = message.content.get("command")
        if command == "reset":
            await self.reset()
        elif command == "status":
            await self.send_message(
                message.sender,
                MessageType.STATUS,
                {"status": self.status.value, "metrics": self.get_metrics()}
            )
    
    async def _handle_query(self, message: AgentMessage) -> None:
        """Handle query messages"""
        query = message.content.get("query")
        context = message.content.get("context")
        response = await self.execute(query, context)
        await self.send_message(
            message.sender,
            MessageType.RESPONSE,
            {"response": response.model_dump()}
        )
    
    async def reset(self) -> None:
        """Reset agent to initial state"""
        self.status = AgentStatus.IDLE
        self.metrics = AgentMetrics()
        self.message_history.clear()
        self.current_task_id = None
        logger.info(f"{self.name} has been reset")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current agent metrics"""
        return {
            "agent_id": self.id,
            "agent_name": self.name,
            "role": self.role.value,
            "status": self.status.value,
            "total_requests": self._total_requests,
            "successful_requests": self._successful_requests,
            "failed_requests": self._failed_requests,
            "success_rate": self._successful_requests / self._total_requests if self._total_requests > 0 else 0,
            "current_metrics": {
                "processing_time_ms": self.metrics.processing_time_ms,
                "tokens_used": self.metrics.tokens_used,
                "api_calls_made": self.metrics.api_calls_made,
                "errors_count": self.metrics.errors_count,
                "retry_count": self.metrics.retry_count
            }
        }
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id}, role={self.role.value}, status={self.status.value})>"