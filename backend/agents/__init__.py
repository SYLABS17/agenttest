from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AgentResponse:
  """Normalized payload returned by each worker agent."""

  agent: str
  query: str
  summary: str
  citations: List[str] = field(default_factory=list)
  latency_ms: int = 0
  relevance: float = 0.0
  metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentMessage:
  """Represents a chat-style message propagated to the UI."""

  role: str
  content: str
  agent: str
  latency_ms: int = 0
  citations: List[str] = field(default_factory=list)
