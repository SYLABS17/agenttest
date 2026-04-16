# Learning Management System - Azure Implementation

Multi-modal RAG system across multiple regional languages, powered by Azure AI services.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Microsoft Azure                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │ AKS          │───▶│ Azure AI     │───▶│ Azure AI Search      │  │
│  │ (API Layer)  │    │ Agent Service│    │ (Hybrid Vector/BM25) │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
│         │                   │                      │               │
│         │                   │                      │               │
│         ▼                   ▼                      ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │ Azure        │    │ Azure OpenAI │    │ Azure Blob Storage   │  │
│  │ Translator   │    │ GPT-4o       │    │ (Content + Frames)   │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Application Insights + Azure Monitor                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Azure Services Used

| Component | Azure Service |
|-----------|---------------|
| Vector Search | Azure AI Search (Hybrid) |
| Embeddings | Azure OpenAI (text-embedding-ada-002) |
| Translation | Azure Translator + Custom Glossary |
| LLM | Azure OpenAI (GPT-4o / GPT-4o-mini) |
| Video Processing | Azure Video Indexer |
| Storage | Azure Blob Storage |
| Compute | Azure Kubernetes Service (AKS) |
| Monitoring | Application Insights |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure credentials

# Run the API
uvicorn src.api.app:app --reload

# Run tests
pytest tests/
```

## Key Metrics

- **Total Students**: 500 Million
- **Daily Active Users**: 120 Million
- **Languages Supported**: 15+
- **P95 Latency**: < 3 seconds
- **Cost Per Query**: $0.02

## Project Structure

```
azure-lms/
├── src/
│   ├── config/          # Azure-specific configuration
│   ├── glossary/        # Academic glossary (10,000+ terms)
│   ├── translation/     # Azure Translator integration
│   ├── chunking/        # Document chunking
│   ├── search/          # Azure AI Search integration
│   ├── reranking/       # Cross-encoder reranking
│   ├── video/           # Azure Video Indexer
│   ├── generation/      # Azure OpenAI generation
│   ├── evaluation/      # Quality framework
│   ├── pipeline/        # Main orchestrator
│   └── api/             # FastAPI application
├── tests/
├── data/glossary/
├── requirements.txt
└── README.md
```

## License

MIT License
