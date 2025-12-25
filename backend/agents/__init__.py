from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class AgentResponse:
    agent: str
    query: str
    content: str
    insights: List[str]
    sources: List[str]
    topics: List[str]
    latency_ms: float
    raw_payload: dict
    timestamp: datetime
