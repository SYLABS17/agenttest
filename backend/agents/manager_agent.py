from backend.agents.bing_agent import BingSearchAgent
from backend.agents.ai_search_agent import AISearchAgent
import asyncio

class ManagerAgent:
    def __init__(self):
        self.bing_agent = BingSearchAgent()
        self.ai_agent = AISearchAgent()

    async def process_request(self, query: str):
        # Coordinate agents
        task1 = self.bing_agent.search(query)
        task2 = self.ai_agent.search(query)
        
        results = await asyncio.gather(task1, task2)
        
        bing_res = results[0]
        ai_res = results[1]
        
        # Aggregate and generate report
        report = self._generate_report(query, bing_res, ai_res)
        return report

    def _generate_report(self, query, bing_res, ai_res):
        # In a real system, this would use an LLM to synthesize
        report = {
            "title": f"Research Report: {query}",
            "sections": [
                {
                    "heading": "Bing Search Insights",
                    "content": bing_res.get("results", [])
                },
                {
                    "heading": "Internal Knowledge (AI Search)",
                    "content": ai_res.get("results", [])
                },
                {
                    "heading": "Conclusion",
                    "content": "Based on the gathered information, this topic is multi-faceted..."
                }
            ],
            "metadata": {
                "agents_involved": ["BingSearchAgent", "AISearchAgent"],
                "status": "completed"
            }
        }
        return report
