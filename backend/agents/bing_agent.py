import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from backend.agents import AgentResponse
from backend.config import AppConfig
from backend.services.observability import ObservabilityService


class BingSearchAgent:
    """Simulated Bing search agent that serves curated research snippets."""

    def __init__(self, settings: AppConfig, observability: ObservabilityService):
        self.settings = settings
        self.observability = observability
        self.name = "bing-search"
        self.dataset_path = Path(settings.data_dir) / "bing_results.json"
        self.dataset = self._load_dataset()

    def _load_dataset(self) -> List[Dict[str, Any]]:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Missing Bing dataset at {self.dataset_path}")
        return json.loads(self.dataset_path.read_text())

    def _pick_entry(self, query: str) -> Dict[str, Any]:
        lowered = query.lower()
        for entry in self.dataset:
            if entry["query"].lower() in lowered:
                return entry
        return self.dataset[0]

    def _simulate_latency(self) -> float:
        if not self.settings.enable_mock_latency:
            return 15.0
        return round(random.uniform(120, 320), 2)

    def run(self, query: str) -> AgentResponse:
        start = time.perf_counter()
        entry = self._pick_entry(query)
        latency = self._simulate_latency()
        time.sleep(latency / 1000.0 if self.settings.enable_mock_latency else 0)
        duration_ms = (time.perf_counter() - start) * 1000
        response = AgentResponse(
            agent=self.name,
            query=query,
            content=entry["summary"],
            insights=entry.get("insights", []),
            sources=entry.get("sources", []),
            topics=entry.get("topics", []),
            latency_ms=round(duration_ms, 2),
            raw_payload=entry,
            timestamp=datetime.now(timezone.utc),
        )
        self.observability.log_dependency(
            name=self.name,
            target="bing.microsoft.com",
            duration_ms=response.latency_ms,
            success=True,
            metadata={"resultCount": len(entry.get("insights", []))},
        )
        return response
