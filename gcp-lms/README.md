# Learning Management System - GCP Implementation

Multi-modal RAG system across multiple regional languages, powered by Google Cloud AI services.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Google Cloud Platform                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │ Cloud Run /  │───▶│ Vertex AI    │───▶│ Vertex AI Search     │  │
│  │ GKE Autopilot│    │ Agent Builder│    │ (Hybrid Vector/BM25) │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
│         │                   │                      │               │
│         │                   │                      │               │
│         ▼                   ▼                      ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │ Cloud        │    │ Gemini 2.0   │    │ Cloud Storage        │  │
│  │ Translation  │    │ Flash        │    │ (Content + Frames)   │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Cloud Monitoring + Cloud Logging + Cloud Trace               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## GCP Services Used

| Component | GCP Service |
|-----------|-------------|
| Vector Search | Vertex AI Search + Vector Search |
| Embeddings | Vertex AI (text-embedding-005 / Gemini Embedding) |
| Translation | Cloud Translation API + Custom Glossary |
| LLM | Vertex AI Generative AI (Gemini 2.0 Flash / Gemini 2.5 Pro) |
| Video Processing | Video Intelligence API + Speech-to-Text |
| Storage | Cloud Storage |
| Compute | Cloud Run / GKE Autopilot |
| Monitoring | Cloud Monitoring + Cloud Logging |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure GCP
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT=your-project-id

# Configure environment
cp .env.example .env
# Edit .env with your settings

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
gcp-lms/
├── src/
│   ├── config/          # GCP-specific configuration
│   ├── glossary/        # Academic glossary (10,000+ terms)
│   ├── translation/     # Cloud Translation integration
│   ├── chunking/        # Document chunking
│   ├── search/          # Vertex AI Search integration
│   ├── reranking/       # Cross-encoder reranking
│   ├── video/           # Video Intelligence API
│   ├── generation/      # Vertex AI Gemini generation
│   ├── evaluation/      # Quality framework
│   ├── pipeline/        # Main orchestrator
│   └── api/             # FastAPI application
├── tests/
├── data/glossary/
├── requirements.txt
└── README.md
```

## GCP vs Azure Comparison

| Aspect | GCP | Azure |
|--------|-----|-------|
| Vector Search | Vertex AI Search | Azure AI Search |
| LLM | Gemini 2.0 Flash | GPT-4o |
| Embeddings | text-embedding-005 | text-embedding-ada-002 |
| Translation | Cloud Translation | Azure Translator |
| Video | Video Intelligence API | Video Indexer |

## License

MIT License
