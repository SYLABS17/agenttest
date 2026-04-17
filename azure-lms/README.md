# Learning Management System - Azure AI Foundry + Voice Live

Simplified LMS using Azure AI Foundry for RAG and Azure Voice Live for speech interactions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Microsoft Azure                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Azure AI Foundry                          │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐  │  │
│  │  │ AI Agents  │──│ GPT-4o     │──│ Azure AI Search (RAG)  │  │  │
│  │  └────────────┘  └────────────┘  └────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              │                                      │
│                              ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Azure Voice Live                          │  │
│  │  ┌────────────────┐  ┌─────────────────────────────────────┐ │  │
│  │  │ Speech-to-Text │  │ Text-to-Speech (Neural Voices)     │ │  │
│  │  └────────────────┘  └─────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Azure Services

| Component | Azure Service |
|-----------|---------------|
| AI Platform | Azure AI Foundry |
| RAG Search | Azure AI Search |
| LLM | GPT-4o |
| Speech Recognition | Azure Speech (Voice Live) |
| Text-to-Speech | Azure Neural Voices |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Azure credentials

# Run the API
uvicorn azure_lms.src.api.app:app --reload
```

## API Endpoints

### Query (RAG)
```bash
POST /api/v1/query
{
  "question": "What is photosynthesis?",
  "language": "en"
}
```

### Text-to-Speech
```bash
POST /api/v1/synthesize
{
  "text": "Hello, welcome to the learning system",
  "language": "en"
}
```

### Real-time Voice (WebSocket)
```javascript
ws://localhost:8000/ws/voice

// Send: {"type": "recognize", "language": "en"}
// Receive: {"type": "transcription", "text": "..."}

// Send: {"type": "query", "text": "What is DNA?"}
// Receive: {"type": "answer", "text": "..."}

// Send: {"type": "speak", "text": "Hello", "language": "hi"}
// Receive: <audio bytes>
```

## Project Structure

```
azure-lms/
├── src/
│   ├── config/      # Settings
│   ├── foundry/     # Azure AI Foundry client
│   ├── voice/       # Azure Voice Live
│   └── api/         # FastAPI application
├── requirements.txt
└── README.md
```

## Supported Languages

English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia, Assamese, Urdu

## License

MIT License
