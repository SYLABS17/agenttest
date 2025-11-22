import json
import os
import random
from backend.config import config

class BingSearchAgent:
    def __init__(self):
        self.simulate = config.SIMULATE_AGENTS
        self.data_path = os.path.join(os.path.dirname(__file__), "../../test/data/bing_results.json")

    async def search(self, query: str):
        if self.simulate:
            return self._get_simulated_response(query)
        else:
            # Real implementation placeholder
            return {"source": "Bing", "query": query, "results": "Real Bing search not implemented in this demo."}

    def _get_simulated_response(self, query: str):
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, "r") as f:
                    data = json.load(f)
                    # return random result or matching query if possible
                    return data.get(query, {"source": "Bing", "query": query, "results": ["Simulated result for " + query]})
            else:
                 return {"source": "Bing", "query": query, "results": ["No dummy data found."]}
        except Exception as e:
            return {"error": str(e)}
