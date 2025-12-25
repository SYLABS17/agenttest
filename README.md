# 🚀 AI Research System

A complete full-stack AI-powered research system hosted on Azure with multi-agent orchestration, beautiful React frontend, and comprehensive observability.

![Architecture](https://img.shields.io/badge/Architecture-Azure-blue)
![Backend](https://img.shields.io/badge/Backend-FastAPI-green)
![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Tailwind-cyan)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🎯 Overview

The AI Research System is an enterprise-grade research platform that leverages multi-agent orchestration to conduct comprehensive research by combining web search (Bing) and knowledge base search (Azure AI Search) capabilities. The system features:

- **Multi-Agent Orchestration**: Manager agent coordinates specialized search agents
- **Dual Search Sources**: Web search via Bing API and semantic search via Azure AI Search
- **Real-time Collaboration**: Group chat-style agent interaction
- **Performance Evaluation**: Built-in agent performance metrics and evaluation
- **Beautiful UI**: Modern, responsive React frontend with dark mode support
- **Comprehensive Monitoring**: Azure Application Insights integration
- **Production Ready**: Full CI/CD pipeline, testing, and deployment automation

## 📚 Table of Contents

- [Architecture](#-architecture)
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Development Setup](#-development-setup)
- [Deployment](#-deployment)
- [Testing](#-testing)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Monitoring](#-monitoring)
- [Contributing](#-contributing)

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Azure Cloud                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   App Service │  │ Azure AI     │  │  Azure       │    │
│  │   (Backend)   │  │   Search     │  │  Storage     │    │
│  │              │  │              │  │  (Frontend)   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│         │                 │                  │             │
│         └─────────────────┼──────────────────┘             │
│                          │                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Azure      │  │ Application  │  │   Azure      │    │
│  │   OpenAI     │  │  Insights    │  │  Key Vault   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘

                          ▲
                          │ HTTPS
                          ▼
                    
┌─────────────────────────────────────────────────────────────┐
│                      Agent System                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│     ┌────────────────────────────────────────┐            │
│     │          Manager Agent                   │            │
│     │     (Orchestration & Synthesis)          │            │
│     └────────────┬──────────────┬──────────────┘            │
│                  ▼              ▼                          │
│     ┌──────────────────┐  ┌──────────────────┐            │
│     │  Bing Search     │  │   AI Search      │            │
│     │     Agent        │  │     Agent        │            │
│     └──────────────────┘  └──────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## ✨ Features

### Core Features
- 🤖 **Multi-Agent Research**: Intelligent coordination between search agents
- 🔍 **Dual Search Sources**: Web and knowledge base search
- 📊 **Performance Metrics**: Real-time agent evaluation and scoring
- 💬 **Chat Interface**: Group chat-style agent collaboration
- 📈 **Analytics Dashboard**: Comprehensive metrics and visualizations
- 🌓 **Dark Mode**: Beautiful UI with theme switching
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile

### Technical Features
- ⚡ **Fast Response**: Optimized async processing
- 🔒 **Secure**: Azure security best practices
- 📝 **Comprehensive Logging**: Structured logging with Azure Monitor
- 🧪 **Well Tested**: Unit, integration, and E2E tests
- 🚀 **CI/CD Ready**: GitHub Actions workflow included
- 📖 **API Documentation**: Auto-generated OpenAPI docs
- 🎯 **Type Safe**: TypeScript frontend, Pydantic backend

## 📋 Prerequisites

### Required Tools
- **Azure Subscription** with sufficient credits
- **Azure CLI** (>= 2.50.0)
- **Python** (>= 3.11)
- **Node.js** (>= 18.x)
- **Git**

### Azure Resources (Auto-provisioned)
- Azure App Service (Linux, Python 3.11)
- Azure Cognitive Search (Standard tier)
- Azure OpenAI Service
- Azure Storage Account
- Application Insights
- Log Analytics Workspace
- Azure Key Vault

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/ai-research-system.git
cd ai-research-system
```

### 2. Set Up Azure Credentials
```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "Your Subscription Name"
```

### 3. Deploy Everything
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Deploy infrastructure
cd scripts
./deploy_resources.sh dev

# Deploy backend
./deploy_backend.sh dev

# Deploy frontend
./deploy_frontend.sh dev

# Validate deployment
./validate_end_to_end.sh dev
```

## 💻 Development Setup

### Backend Development

1. **Set up Python environment**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp ../.env.template .env
# Edit .env with your Azure credentials
```

3. **Run locally**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. **Access API**:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend Development

1. **Install dependencies**:
```bash
cd frontend
npm install
```

2. **Configure environment**:
```bash
# Create .env.local
echo "VITE_API_URL=http://localhost:8000" > .env.local
```

3. **Run development server**:
```bash
npm run dev
```

4. **Access UI**: http://localhost:3000

## 🚢 Deployment

### Manual Deployment

Use the provided scripts in the `/scripts` directory:

```bash
# Deploy all components
./scripts/deploy_resources.sh [dev|test|prod]
./scripts/deploy_backend.sh [dev|test|prod]
./scripts/deploy_frontend.sh [dev|test|prod]
./scripts/validate_end_to_end.sh [dev|test|prod]
```

### CI/CD Deployment

The GitHub Actions workflow automatically deploys on push to main:

1. **Set up GitHub Secrets**:
```bash
# Create service principal
az ad sp create-for-rbac --name "github-actions" --role contributor \
  --scopes /subscriptions/{subscription-id} \
  --sdk-auth
```

2. **Add secret to GitHub**:
- Go to Settings → Secrets → Actions
- Add `AZURE_CREDENTIALS` with the service principal JSON

3. **Push to trigger deployment**:
```bash
git push origin main
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=. --cov-report=html
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### End-to-End Tests
```bash
./scripts/validate_end_to_end.sh dev
```

## 📖 API Documentation

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint with service info |
| `/health` | GET | Health check endpoint |
| `/api/research` | POST | Submit research query |
| `/api/metrics` | GET | Get system metrics |
| `/api/agents/status` | GET | Get agent status |
| `/api/evaluation/history` | GET | Get evaluation history |
| `/api/logs` | GET | Get recent logs (dev only) |

### Example Research Request

```bash
curl -X POST https://your-app.azurewebsites.net/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Future of renewable energy in Africa",
    "include_evaluation": true
  }'
```

## ⚙️ Configuration

### Environment Variables

See `.env.template` for all configuration options. Key variables:

- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint
- `AZURE_SEARCH_ENDPOINT`: Your Azure AI Search endpoint
- `BING_SEARCH_API_KEY`: Bing Search API key
- `APPLICATIONINSIGHTS_CONNECTION_STRING`: App Insights connection
- `ENABLE_DUMMY_MODE`: Use dummy data for testing

### ARM Template Parameters

Edit `/infra/parameters.json` to customize:
- Resource SKUs
- Location
- Tags
- Scaling options

## 📊 Monitoring

### Application Insights

1. **Access Portal**: Azure Portal → Application Insights → Your Instance
2. **View Metrics**: Performance, failures, dependencies
3. **Live Metrics**: Real-time monitoring
4. **Logs**: KQL queries for detailed analysis

### Custom Metrics

The system tracks:
- Agent query counts
- Response latencies
- Success/failure rates
- Agreement scores
- Evaluation metrics

### Alerts

Configure alerts in Azure Portal for:
- High latency (> 5s)
- Error rate (> 5%)
- Resource utilization (> 80%)

## 🤝 Contributing

### Development Workflow

1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** Pull Request

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **TypeScript**: Use ESLint, Prettier
- **Commits**: Follow conventional commits

### Testing Requirements

- Maintain > 80% code coverage
- All tests must pass
- Add tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Azure AI Services for powerful AI capabilities
- FastAPI for excellent Python web framework
- React team for amazing frontend library
- Tailwind CSS for beautiful styling
- Open source community for invaluable tools

## 📞 Support

- **Documentation**: See `/docs` folder
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@example.com

## 🎯 Roadmap

- [ ] Add more agent types (News, Academic, Patent)
- [ ] Implement caching layer (Redis)
- [ ] Add authentication (Azure AD B2C)
- [ ] Multi-language support
- [ ] Export reports to PDF/Word
- [ ] Real-time WebSocket updates
- [ ] Mobile applications (React Native)
- [ ] Advanced visualizations (D3.js)

---

Built with ❤️ using Azure AI and modern web technologies