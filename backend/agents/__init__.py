"""
Agent module for AI Research System
"""

from .base_agent import BaseAgent, AgentResponse, AgentRole, AgentStatus
from .manager_agent import ManagerAgent
from .bing_agent import BingSearchAgent
from .ai_search_agent import AISearchAgent

__all__ = [
    "BaseAgent",
    "AgentResponse",
    "AgentRole",
    "AgentStatus",
    "ManagerAgent",
    "BingSearchAgent",
    "AISearchAgent",
]