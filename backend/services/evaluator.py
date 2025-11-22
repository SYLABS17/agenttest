import random
import time

class Evaluator:
    def evaluate_response(self, query, report):
        # Dummy metrics
        latency = random.uniform(0.5, 2.0)
        accuracy = random.uniform(0.8, 0.99)
        relevance = random.uniform(0.7, 1.0)
        
        score = {
            "query": query,
            "metrics": {
                "latency_seconds": latency,
                "accuracy_score": accuracy,
                "relevance_score": relevance
            },
            "timestamp": time.time()
        }
        return score
