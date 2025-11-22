import axios, { AxiosInstance, AxiosError } from 'axios';
import toast from 'react-hot-toast';

// Create axios instance with default config
const api: AxiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  timeout: 60000, // 60 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('auth_token');
      window.location.href = '/';
    } else if (error.response?.status === 500) {
      toast.error('Server error. Please try again later.');
    } else if (error.code === 'ECONNABORTED') {
      toast.error('Request timeout. Please try again.');
    }
    
    return Promise.reject(error);
  }
);

// API endpoints
export const researchAPI = {
  // Conduct research
  conductResearch: async (query: string, context?: any, evaluate: boolean = true) => {
    const response = await api.post('/research', {
      query,
      context,
      evaluate,
      timeout_seconds: 30,
    });
    return response.data;
  },
  
  // Get test queries
  getTestQueries: async () => {
    const response = await api.get('/test/queries');
    return response.data;
  },
  
  // Simulate research with test query
  simulateResearch: async (queryIndex: number) => {
    const response = await api.post(`/test/simulate?query_index=${queryIndex}`);
    return response.data;
  },
};

export const agentAPI = {
  // Get all agents
  getAgents: async () => {
    const response = await api.get('/agents');
    return response.data;
  },
  
  // Reset agents
  resetAgents: async () => {
    const response = await api.post('/agents/reset');
    return response.data;
  },
};

export const metricsAPI = {
  // Get metrics
  getMetrics: async () => {
    const response = await api.get('/metrics');
    return response.data;
  },
  
  // Get evaluation history
  getEvaluationHistory: async (limit: number = 10) => {
    const response = await api.get(`/evaluation/history?limit=${limit}`);
    return response.data;
  },
  
  // Export evaluation
  exportEvaluation: async (evaluationId: number, format: string = 'json') => {
    const response = await api.post(`/evaluation/export?evaluation_id=${evaluationId}&format=${format}`);
    return response.data;
  },
};

export const systemAPI = {
  // Health check
  healthCheck: async () => {
    const response = await api.get('/healthz');
    return response.data;
  },
  
  // Get configuration
  getConfig: async () => {
    const response = await api.get('/config');
    return response.data;
  },
};

export default api;