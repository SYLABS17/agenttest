# Learning Management System - AWS Implementation

Multi-modal RAG system across multiple regional languages, powered by AWS AI services.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Amazon Web Services                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │ EKS / Lambda │───▶│ Amazon       │───▶│ Amazon OpenSearch    │  │
│  │ (API Layer)  │    │ Bedrock      │    │ (Hybrid Vector/BM25) │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
│         │                   │                      │               │
│         │                   │                      │               │
│         ▼                   ▼                      ▼               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │ Amazon       │    │ Bedrock      │    │ Amazon S3            │  │
│  │ Translate    │    │ Claude/Titan │    │ (Content + Frames)   │  │
│  └──────────────┘    └──────────────┘    └──────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ CloudWatch + X-Ray                                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## AWS Services Used

| Component | AWS Service |
|-----------|-------------|
| Vector Search | Amazon OpenSearch Serverless / Amazon Kendra |
| Embeddings | Amazon Bedrock (Titan Embeddings) |
| Translation | Amazon Translate + Custom Terminology |
| LLM | Amazon Bedrock (Claude 3.5 / Titan) |
| Video Processing | Amazon Transcribe + Rekognition Video |
| Storage | Amazon S3 |
| Compute | Amazon EKS / Lambda |
| Monitoring | CloudWatch + X-Ray |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure AWS
aws configure

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
aws-lms/
├── src/
│   ├── config/          # AWS-specific configuration
│   ├── glossary/        # Academic glossary (10,000+ terms)
│   ├── translation/     # Amazon Translate integration
│   ├── chunking/        # Document chunking
│   ├── search/          # OpenSearch integration
│   ├── reranking/       # Cross-encoder reranking
│   ├── video/           # Amazon Transcribe
│   ├── generation/      # Bedrock generation
│   ├── evaluation/      # Quality framework
│   ├── pipeline/        # Main orchestrator
│   └── api/             # FastAPI application
├── tests/
├── data/glossary/
├── requirements.txt
└── README.md
```

## Cloud Comparison

| Aspect | AWS | Azure | GCP |
|--------|-----|-------|-----|
| Vector Search | OpenSearch | AI Search | Vertex AI Search |
| LLM | Bedrock Claude | GPT-4o | Gemini 2.0 |
| Embeddings | Titan Embeddings | ada-002 | text-embedding-005 |
| Translation | Translate | Translator | Translation API |
| Video | Transcribe | Video Indexer | Video Intelligence |

## License

MIT License
