import { useState, useEffect } from 'react'
import { ArrowPathIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import { apiService, MetricsResponse } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

export default function MetricsPage() {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null)
  const [agentStatus, setAgentStatus] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(false)

  useEffect(() => {
    fetchMetrics()
    fetchAgentStatus()
    
    let interval: NodeJS.Timeout | null = null
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchMetrics()
        fetchAgentStatus()
      }, 5000)
    }
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [autoRefresh])

  const fetchMetrics = async () => {
    try {
      const data = await apiService.getMetrics()
      setMetrics(data)
      setError(null)
    } catch (err: any) {
      setError('Failed to fetch metrics')
      console.error(err)
    }
  }

  const fetchAgentStatus = async () => {
    try {
      const data = await apiService.getAgentsStatus()
      setAgentStatus(data)
      setIsLoading(false)
    } catch (err: any) {
      console.error(err)
      setIsLoading(false)
    }
  }

  const handleExport = async () => {
    try {
      const blob = await apiService.exportEvaluations()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `metrics_${new Date().toISOString().split('T')[0]}.csv`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Export failed:', err)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

  // Prepare agent metrics for charts
  const agentMetricsData = metrics?.agents ? 
    Object.entries(metrics.agents).map(([name, data]: [string, any]) => ({
      name: name.replace('_agent', '').replace('_', ' '),
      queries: data.total_queries || 0,
      success: data.successful_queries || 0,
      failed: data.failed_queries || 0,
      avgLatency: data.average_latency_ms || 0,
    })) : []

  // Prepare evaluation metrics
  const evaluationData = metrics?.evaluations?.metrics ? 
    Object.entries(metrics.evaluations.metrics).map(([metric, data]: [string, any]) => ({
      metric,
      mean: data.mean || 0,
      median: data.median || 0,
      count: data.count || 0,
    })) : []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              System Metrics & Performance
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Real-time monitoring of agent performance and system health
            </p>
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`btn-secondary flex items-center ${autoRefresh ? 'bg-primary-100 dark:bg-primary-900/30' : ''}`}
            >
              <ArrowPathIcon className={`h-5 w-5 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
              {autoRefresh ? 'Auto-refreshing' : 'Auto-refresh'}
            </button>
            
            <button
              onClick={handleExport}
              className="btn-secondary flex items-center"
            >
              <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
              Export CSV
            </button>
          </div>
        </div>
        
        {error && (
          <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
          </div>
        )}
      </div>

      {/* Agent Status Grid */}
      {agentStatus && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(agentStatus.agents || {}).map(([name, status]: [string, any]) => (
            <div key={name} className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-4">
              <div className="flex justify-between items-center mb-3">
                <h3 className="font-medium text-gray-900 dark:text-white">
                  {name.replace('_', ' ')}
                </h3>
                <span className={`badge ${status.healthy ? 'badge-success' : 'badge-error'}`}>
                  {status.healthy ? 'Healthy' : 'Error'}
                </span>
              </div>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Status:</span>
                  <span className="text-gray-900 dark:text-white">{status.status || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Total Queries:</span>
                  <span className="text-gray-900 dark:text-white">{status.total_queries || 0}</span>
                </div>
                {status.dummy_mode !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Mode:</span>
                    <span className="text-gray-900 dark:text-white">
                      {status.dummy_mode ? 'Dummy' : 'Live'}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Query Distribution */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Agent Query Distribution
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={agentMetricsData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="queries"
              >
                {agentMetricsData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Average Latency */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Average Latency by Agent
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={agentMetricsData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value: number) => `${value.toFixed(0)}ms`} />
              <Line 
                type="monotone" 
                dataKey="avgLatency" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={{ fill: '#3b82f6' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Evaluation Metrics */}
      {evaluationData.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Evaluation Metrics Performance
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={evaluationData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="metric" />
              <YAxis domain={[0, 1]} />
              <Tooltip formatter={(value: number) => (value * 100).toFixed(1) + '%'} />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="mean" 
                stroke="#3b82f6" 
                fill="#3b82f6" 
                fillOpacity={0.3}
              />
              <Area 
                type="monotone" 
                dataKey="median" 
                stroke="#10b981" 
                fill="#10b981" 
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* System Information */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          System Information
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-gray-600 dark:text-gray-400">Timestamp:</span>
            <p className="font-medium text-gray-900 dark:text-white">
              {metrics?.timestamp ? new Date(metrics.timestamp).toLocaleString() : 'N/A'}
            </p>
          </div>
          <div>
            <span className="text-gray-600 dark:text-gray-400">Total Evaluations:</span>
            <p className="font-medium text-gray-900 dark:text-white">
              {metrics?.evaluations?.total_evaluations || 0}
            </p>
          </div>
          <div>
            <span className="text-gray-600 dark:text-gray-400">Tracing:</span>
            <p className="font-medium text-gray-900 dark:text-white">
              {metrics?.observability?.tracing_enabled ? 'Enabled' : 'Disabled'}
            </p>
          </div>
          <div>
            <span className="text-gray-600 dark:text-gray-400">App Insights:</span>
            <p className="font-medium text-gray-900 dark:text-white">
              {metrics?.observability?.has_app_insights ? 'Connected' : 'Not Connected'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}