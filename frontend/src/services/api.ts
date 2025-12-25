import axios, { AxiosError } from 'axios'

// Create axios instance with default config
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 60000, // 1 minute timeout for research queries
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for adding auth token if needed
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

// Types
export interface ResearchQuery {
  query: string
  context?: Record<string, any>
  include_evaluation?: boolean
}

export interface ResearchResponse {
  success: boolean
  query: string
  report?: string
  chat_history?: ChatMessage[]
  evaluation?: EvaluationReport
  error?: string
  processing_time_ms: number
}

export interface ChatMessage {
  id: string
  agent_name: string
  content: string
  metadata: Record<string, any>
  timestamp: string
}

export interface EvaluationReport {
  query: string
  timestamp: string
  agent_evaluations: AgentEvaluation[]
  agreement_score: number
  summary: EvaluationSummary
  recommendations: string[]
}

export interface AgentEvaluation {
  agent_name: string
  query: string
  timestamp: string
  latency_ms: number
  scores: {
    accuracy: number
    latency: number
    relevance: number
    completeness: number
  }
  overall_score: number
}

export interface EvaluationSummary {
  overall: {
    mean: number
    median: number
    best_agent: string
    agreement_score: number
  }
  latency: {
    mean_ms: number
    median_ms: number
    total_ms: number
  }
}

export interface HealthResponse {
  status: string
  timestamp: string
  environment: string
  agents: Record<string, any>
  services: Record<string, any>
}

export interface MetricsResponse {
  timestamp: string
  agents: Record<string, any>
  evaluations: Record<string, any>
  observability: Record<string, any>
}

export interface LogEntry {
  timestamp?: string
  level?: string
  logger?: string
  message?: string
  raw?: string
}

// API Methods
export const apiService = {
  // Health check
  async getHealth(): Promise<HealthResponse> {
    const { data } = await api.get<HealthResponse>('/api/health')
    return data
  },

  // Research
  async conductResearch(query: ResearchQuery): Promise<ResearchResponse> {
    const { data } = await api.post<ResearchResponse>('/api/research', query)
    return data
  },

  // Metrics
  async getMetrics(): Promise<MetricsResponse> {
    const { data } = await api.get<MetricsResponse>('/api/metrics')
    return data
  },

  // Agent status
  async getAgentsStatus(): Promise<Record<string, any>> {
    const { data } = await api.get('/api/agents/status')
    return data
  },

  // Evaluation
  async getEvaluationHistory(limit: number = 100): Promise<{
    count: number
    evaluations: AgentEvaluation[]
  }> {
    const { data } = await api.get(`/api/evaluation/history?limit=${limit}`)
    return data
  },

  async exportEvaluations(): Promise<Blob> {
    const response = await api.get('/api/evaluation/export', {
      responseType: 'blob'
    })
    return response.data
  },

  // Logs (dev only)
  async getRecentLogs(lines: number = 100): Promise<{
    log_file: string
    total_lines: number
    returned_lines: number
    logs: LogEntry[]
  }> {
    const { data } = await api.get(`/api/logs?lines=${lines}`)
    return data
  },

  // Test with dummy query
  async testDummyQuery(): Promise<ResearchResponse> {
    const { data } = await api.post<ResearchResponse>('/api/test/dummy-query')
    return data
  },
}

export default api