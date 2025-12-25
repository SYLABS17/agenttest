from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from backend.agents import AgentResponse
from backend.config import AppConfig
from backend.services.evaluator import AgentEvaluator
from backend.services.observability import ObservabilityService


class ManagerAgent:
    """Coordinates research workflow and synthesises the final report."""

    def __init__(
        self,
        settings: AppConfig,
        observability: ObservabilityService,
        bing_agent,
        ai_search_agent,
        evaluator: AgentEvaluator,
    ):
        self.settings = settings
        self.observability = observability
        self.bing_agent = bing_agent
        self.ai_search_agent = ai_search_agent
        self.evaluator = evaluator
        self.reports_dir = Path(settings.reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def run_research(self, query: str) -> Dict:
        conversation: List[Dict] = []
        self.observability.log_event("research_received", query=query)

        with self.observability.span("manager.research") as span:
            conversation.append(self._manager_message(f"Received query: '{query}'"))
            bing_response = self.bing_agent.run(query)
            conversation.append(self._agent_message(bing_response))

            ai_response = self.ai_search_agent.run(query)
            conversation.append(self._agent_message(ai_response))

            merged_report = self._compose_report(query, [bing_response, ai_response])
            conversation.append(self._manager_message("Synthesised final research report."))

            evaluation_payloads = [self._response_dict(resp) for resp in [bing_response, ai_response]]
            evaluation = self.evaluator.evaluate(evaluation_payloads)

            if span:
                span.add_attribute("custom.query", query)
                span.add_attribute("custom.agentCount", 2)

        report_path = self._persist_report(query, merged_report)
        self.observability.log_event(
            "report_persisted",
            query=query,
            reportPath=str(report_path),
            agents=[resp.agent for resp in [bing_response, ai_response]],
        )

        return {
            "query": query,
            "conversation": conversation,
            "final_report": merged_report,
            "latency": {
                bing_response.agent: bing_response.latency_ms,
                ai_response.agent: ai_response.latency_ms,
            },
            "evaluation": {
                agent: result.__dict__ for agent, result in evaluation.items()
            },
            "generated_at": self._utc_timestamp(),
            "report_path": str(report_path),
        }

    def _manager_message(self, message: str) -> Dict:
        return {
            "sender": "manager",
            "message": message,
            "timestamp": self._utc_timestamp(),
        }

    def _agent_message(self, response: AgentResponse) -> Dict:
        return {
            "sender": response.agent,
            "message": response.content,
            "insights": response.insights,
            "sources": response.sources,
            "timestamp": response.timestamp.isoformat().replace("+00:00", "Z"),
        }

    def _compose_report(self, query: str, responses: List[AgentResponse]) -> Dict:
        combined_insights = []
        combined_sources = []
        topics = set()
        for resp in responses:
            combined_insights.extend(resp.insights)
            combined_sources.extend(resp.sources)
            topics.update(resp.topics)
        unique_sources = list(dict.fromkeys(combined_sources))
        summary = f"The research team analysed {len(responses)} knowledge channels to explore '{query}'."
        return {
            "title": f"Research Brief: {query}",
            "summary": summary,
            "key_insights": combined_insights,
            "sources": unique_sources,
            "topics": sorted(topics),
            "next_steps": [
                "Validate findings with domain experts.",
                "Operationalise promising initiatives in pilot regions.",
                "Instrument telemetry for live monitoring."
            ],
        }

    def _persist_report(self, query: str, report: Dict) -> Path:
        safe_name = query.lower().replace(" ", "_").replace("/", "-")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        path = self.reports_dir / f"{safe_name}_{timestamp}.json"
        path.write_text(json.dumps(report, indent=2))
        return path

    def _response_dict(self, response: AgentResponse) -> Dict:
        return {
            "agent": response.agent,
            "query": response.query,
            "insights": response.insights,
            "topics": response.topics,
            "latency_ms": response.latency_ms,
        }

    @staticmethod
    def _utc_timestamp() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
