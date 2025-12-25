"""Base agent class for all research agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid
import asyncio
from enum import Enum
import structlog

logger = structlog.get_logger()


class AgentStatus(Enum):
    """Agent status enumeration."""
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class AgentMessage:
    """Message structure for agent communication."""
    
    def __init__(self, 
                 agent_name: str,
                 content: str,
                 metadata: Optional[Dict[str, Any]] = None,
                 timestamp: Optional[datetime] = None):
        self.id = str(uuid.uuid4())
        self.agent_name = agent_name
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "agent_name": self.agent_name,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class BaseAgent(ABC):
    """Base class for all research agents."""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize base agent.
        
        Args:
            name: Agent name
            config: Agent configuration
        """
        self.name = name
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self.conversation_history: List[AgentMessage] = []
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "total_latency_ms": 0,
            "average_latency_ms": 0
        }
        self.logger = logger.bind(agent=name)
        
    @abstractmethod
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentMessage:
        """Process a research query.
        
        Args:
            query: Research query to process
            context: Optional context information
            
        Returns:
            Agent response message
        """
        pass
    
    @abstractmethod
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Perform search operation.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        pass
    
    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentMessage:
        """Execute agent processing with metrics and error handling.
        
        Args:
            query: Research query
            context: Optional context
            
        Returns:
            Agent response message
        """
        start_time = datetime.utcnow()
        self.status = AgentStatus.PROCESSING
        self.metrics["total_queries"] += 1
        
        try:
            self.logger.info("Processing query", query=query[:100])
            
            # Process the query
            message = await self.process(query, context)
            
            # Update metrics
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.metrics["successful_queries"] += 1
            self.metrics["total_latency_ms"] += latency_ms
            self.metrics["average_latency_ms"] = (
                self.metrics["total_latency_ms"] / self.metrics["successful_queries"]
            )
            
            # Add performance metadata
            message.metadata["latency_ms"] = latency_ms
            message.metadata["status"] = "success"
            
            # Update conversation history
            self.conversation_history.append(message)
            
            self.status = AgentStatus.COMPLETED
            self.logger.info("Query processed successfully", latency_ms=latency_ms)
            
            return message
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.metrics["failed_queries"] += 1
            
            error_message = f"Error processing query: {str(e)}"
            self.logger.error("Query processing failed", error=str(e), query=query[:100])
            
            # Create error message
            message = AgentMessage(
                agent_name=self.name,
                content=error_message,
                metadata={
                    "status": "error",
                    "error": str(e),
                    "query": query
                }
            )
            
            self.conversation_history.append(message)
            return message
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            **self.metrics,
            "status": self.status.value,
            "history_size": len(self.conversation_history)
        }
    
    def reset_metrics(self):
        """Reset agent metrics."""
        self.metrics = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "total_latency_ms": 0,
            "average_latency_ms": 0
        }
        
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check.
        
        Returns:
            Health status dictionary
        """
        return {
            "agent": self.name,
            "status": self.status.value,
            "healthy": self.status != AgentStatus.ERROR,
            "metrics": self.get_metrics()
        }