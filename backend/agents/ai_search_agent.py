import json
import os
from backend.config import config

class AISearchAgent:
    def __init__(self):
        self.simulate = config.SIMULATE_AGENTS
        self.data_path = os.path.join(os.path.dirname(__file__), "../../test/data/ai_search_results.json")

    async def search(self, query: str):
        if self.simulate:
            return self._get_simulated_response(query)
        else:
            return {"source": "Azure AI Search", "query": query, "results": "Real AI Search not implemented in this demo."}

    def _get_simulated_response(self, query: str):
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, "r") as f:
                    data = json.load(f)
                    return data.get(query, {"source": "Azure AI Search", "query": query, "results": ["Simulated result for " + query]})
            else:
                 return {"source": "Azure AI Search", "query": query, "results": ["No dummy data found."]}
        except Exception as e:
            return {"error": str(e)}
