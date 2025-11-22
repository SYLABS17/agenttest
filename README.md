# AI Research System - Azure Multi-Agent Orchestration Platform

A comprehensive, production-ready AI research system built on Azure that orchestrates multiple AI agents to conduct intelligent research, providing detailed reports with analysis, insights, and recommendations.

![Architecture](https://img.shields.io/badge/Architecture-Microservices-blue)
![Backend](https://img.shields.io/badge/Backend-FastAPI-green)
![Frontend](https://img.shields.io/badge/Frontend-React-blue)
![Cloud](https://img.shields.io/badge/Cloud-Azure-blue)
![AI](https://img.shields.io/badge/AI-Multi--Agent-purple)

## 🌟 Features

- **Multi-Agent Orchestration**: Manager agent coordinates Bing Search and Azure AI Search agents
- **Group Chat Collaboration**: Agents work together in a conversational style
- **Comprehensive Research Reports**: Detailed analysis with sources and recommendations
- **Real-time Observability**: Azure Monitor and Application Insights integration
- **Performance Evaluation**: Built-in agent performance scoring and metrics
- **Modern UI**: React with Tailwind CSS, dark mode, and responsive design
- **Production Ready**: Full CI/CD pipeline, testing, and deployment automation

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Azure Cloud                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐    ┌──────────────┐   ┌────────────┐ │
│  │ React       │───▶│ FastAPI      │──▶│ Manager    │ │
│  │ Frontend    │    │ Backend      │   │ Agent      │ │
│  └──────────────┘    └──────────────┘   └─────┬──────┘ │
│                                                │        │
│                                      ┌─────────┴────┐   │
│                                      ▼              ▼   │
│                              ┌──────────────┐ ┌──────────────┐
│                              │ Bing Search  │ │ AI Search    │
│                              │ Agent        │ │ Agent        │
│                              └──────────────┘ └──────────────┘
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Azure Services                         │  │
│  ├──────────────────────────────────────────────────┤  │
│  │ • App Service      • Cognitive Search            │  │
│  │ • Storage Account  • OpenAI Service              │  │
│  │ • Monitor         • Application Insights         │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Azure Subscription
- Azure CLI installed
- Node.js 18+ and npm
- Python 3.11+
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ai-research-system.git
cd ai-research-system
```

### 2. Configure Environment

```bash
cp .env.template .env
# Edit .env with your Azure credentials and configuration
```

### 3. Deploy to Azure

```bash
# Deploy Azure infrastructure
./scripts/deploy_resources.sh

# Deploy backend
./scripts/deploy_backend.sh

# Deploy frontend
./scripts/deploy_frontend.sh

# Validate deployment
./scripts/validate_end_to_end.sh
```

### 4. Local Development

#### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

## 📁 Project Structure

```
ai-research-system/
├── infra/                      # Azure Infrastructure (ARM/Bicep)
│   ├── main.bicep             # Main infrastructure template
│   ├── resources.bicep        # Resource definitions
│   └── parameters.json        # Deployment parameters
│
├── backend/                    # Python FastAPI Backend
│   ├── agents/                # AI Agent implementations
│   │   ├── base_agent.py     # Base agent class
│   │   ├── manager_agent.py  # Manager orchestrator
│   │   ├── bing_agent.py     # Bing search agent
│   │   └── ai_search_agent.py # Azure AI search agent
│   ├── services/              # Backend services
│   │   ├── observability.py  # Monitoring service
│   │   └── evaluator.py      # Agent evaluation
│   ├── tests/                 # Backend tests
│   ├── main.py               # FastAPI application
│   └── requirements.txt      # Python dependencies
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── stores/          # State management
│   │   ├── services/        # API services
│   │   └── App.tsx          # Main application
│   ├── public/
│   └── package.json
│
├── test/                      # Test data and utilities
│   ├── data/                 # Mock data
│   └── reports/             # Test reports
│
├── scripts/                   # Deployment scripts
│   ├── deploy_resources.sh  # Deploy Azure resources
│   ├── deploy_backend.sh    # Deploy backend
│   ├── deploy_frontend.sh   # Deploy frontend
│   └── validate_end_to_end.sh # E2E validation
│
├── .github/
│   └── workflows/
│       └── deploy.yml        # CI/CD pipeline
│
└── README.md                 # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.template`:

```env
# Azure Configuration
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_RESOURCE_GROUP=ai-research-rg
AZURE_LOCATION=eastus

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Azure Cognitive Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=your-search-key

# Application Settings
APP_ENV=development
APP_DEBUG=true
```

### Azure Resources Configuration

The infrastructure is defined in Bicep templates with parameterized values:

- **App Service Plan**: Configurable SKU (default: P1V2)
- **Storage Account**: Configurable redundancy (default: LRS)
- **Cognitive Search**: Configurable tier (default: Standard)
- **Monitoring**: Application Insights and Log Analytics
- **Security**: Managed Identity, Key Vault, Private Endpoints (optional)

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ --cov=. --cov-report=html
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

### End-to-End Tests
```bash
./scripts/validate_end_to_end.sh
```

## 📊 Observability

### Metrics & Monitoring

- **Application Insights**: Application performance monitoring
- **Azure Monitor**: Infrastructure and resource monitoring
- **Custom Metrics**: Agent performance, latency, success rates
- **Distributed Tracing**: Request flow across services
- **Structured Logging**: JSON formatted logs with correlation

### Accessing Metrics

1. **Azure Portal**: Navigate to Application Insights resource
2. **Backend API**: `GET /metrics` endpoint
3. **Frontend Dashboard**: Observability panel in the UI

## 🤖 Agent System

### Manager Agent
- Orchestrates worker agents
- Creates research plans
- Facilitates group chat collaboration
- Synthesizes findings
- Generates final reports

### Bing Search Agent
- Searches web content
- Retrieves news articles
- Finds academic papers
- Provides relevance scoring

### AI Search Agent
- Queries internal knowledge base
- Performs semantic search
- Uses vector similarity
- Enhances with knowledge graph

### Agent Evaluation
- Performance scoring (accuracy, latency, relevance)
- Completeness assessment
- Confidence calibration
- Agreement analysis

## 🚢 Deployment

### CI/CD Pipeline

The GitHub Actions workflow handles:

1. **Testing**: Backend and frontend tests
2. **Validation**: Infrastructure templates
3. **Deployment**: Staged deployment to environments
4. **Validation**: E2E testing post-deployment

### Manual Deployment

```bash
# Set environment
export ENVIRONMENT=prod

# Deploy all components
./scripts/deploy_resources.sh
./scripts/deploy_backend.sh
./scripts/deploy_frontend.sh

# Validate
./scripts/validate_end_to_end.sh
```

### Environments

- **dev**: Development environment
- **test**: Testing/staging environment
- **prod**: Production environment

## 🔒 Security

- **HTTPS Only**: Enforced for all services
- **Managed Identity**: Azure resource authentication
- **Key Vault**: Secure secret management
- **Private Endpoints**: Network isolation (optional)
- **CORS Configuration**: Controlled cross-origin access
- **Input Validation**: Request sanitization
- **Rate Limiting**: API throttling

## 📈 Performance

- **Caching**: Response caching for repeated queries
- **Async Processing**: Non-blocking agent execution
- **Connection Pooling**: Efficient database connections
- **CDN**: Static asset delivery (frontend)
- **Auto-scaling**: App Service scaling rules
- **Performance Monitoring**: Application Insights profiling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 API Documentation

Once deployed, access the interactive API documentation at:

- **Swagger UI**: `https://your-backend-url/docs`
- **ReDoc**: `https://your-backend-url/redoc`

### Key Endpoints

- `POST /research` - Conduct research with query
- `GET /agents` - List all agents and status
- `GET /metrics` - Get system metrics
- `GET /evaluation/history` - Get evaluation history
- `GET /healthz` - Health check

## 🐛 Troubleshooting

### Common Issues

1. **Deployment Fails**
   - Check Azure subscription and permissions
   - Verify resource quotas
   - Review deployment logs in Azure Portal

2. **Backend Not Responding**
   - Check App Service logs
   - Verify environment variables
   - Test health endpoint: `/healthz`

3. **Frontend Connection Issues**
   - Verify CORS configuration
   - Check API URL in frontend config
   - Review browser console errors

4. **Agent Failures**
   - Check API keys and endpoints
   - Review agent logs in Application Insights
   - Verify Azure service connectivity

### Debug Commands

```bash
# Check backend logs
az webapp log tail --name <app-service-name> --resource-group <rg-name>

# Test backend health
curl https://your-backend-url/healthz

# Check frontend deployment
az storage blob list --account-name <storage-name> --container-name '$web'
```

## 📚 Documentation

- [Backend API Documentation](./backend/README.md)
- [Frontend Documentation](./frontend/README.md)
- [Infrastructure Guide](./infra/README.md)
- [Agent Development Guide](./docs/agents.md)
- [Deployment Guide](./docs/deployment.md)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Azure AI Services team for excellent documentation
- FastAPI community for the amazing framework
- React and Tailwind CSS communities
- OpenAI for GPT models
- Microsoft for Azure cloud platform

## 📞 Support

For issues and questions:
- Open an issue in GitHub
- Check existing issues for solutions
- Review documentation and guides

---

**Built with ❤️ using Azure AI and modern web technologies**