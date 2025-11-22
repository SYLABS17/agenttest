import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    BING_SEARCH_API_KEY = os.getenv("BING_SEARCH_API_KEY", "")
    BING_SEARCH_ENDPOINT = os.getenv("BING_SEARCH_ENDPOINT", "https://api.bing.microsoft.com/v7.0/search")
    
    AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    AZURE_SEARCH_KEY = os.getenv("AZURE_SEARCH_KEY", "")
    AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX", "index")
    
    APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
    
    # Feature flags or simulation modes
    SIMULATE_AGENTS = os.getenv("SIMULATE_AGENTS", "True").lower() == "true"

config = Config()
