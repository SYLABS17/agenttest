import { useState, useEffect, useRef } from 'react'
import { ArrowPathIcon, FunnelIcon } from '@heroicons/react/24/outline'
import { apiService, LogEntry } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState('')
  const [levelFilter, setLevelFilter] = useState('all')
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [lines, setLines] = useState(100)
  const logsEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchLogs()
    
    let interval: NodeJS.Timeout | null = null
    if (autoRefresh) {
      interval = setInterval(fetchLogs, 3000)
    }
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [autoRefresh, lines])

  const fetchLogs = async () => {
    try {
      const data = await apiService.getRecentLogs(lines)
      setLogs(data.logs)
      setError(null)
      setIsLoading(false)
    } catch (err: any) {
      if (err.response?.status === 403) {
        setError('Logs are only available in development mode')
      } else {
        setError('Failed to fetch logs')
      }
      setIsLoading(false)
    }
  }

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const getLogLevelColor = (level?: string) => {
    switch (level?.toUpperCase()) {
      case 'ERROR':
        return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20'
      case 'WARNING':
      case 'WARN':
        return 'text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20'
      case 'INFO':
        return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20'
      case 'DEBUG':
        return 'text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-700/50'
      default:
        return 'text-gray-700 dark:text-gray-300'
    }
  }

  const filteredLogs = logs.filter(log => {
    const matchesText = !filter || 
      log.message?.toLowerCase().includes(filter.toLowerCase()) ||
      log.raw?.toLowerCase().includes(filter.toLowerCase()) ||
      log.logger?.toLowerCase().includes(filter.toLowerCase())
    
    const matchesLevel = levelFilter === 'all' || 
      log.level?.toUpperCase() === levelFilter.toUpperCase()
    
    return matchesText && matchesLevel
  })

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              System Logs
            </h1>
            <p className="text-gray-600 dark:text-gray-400">
              Real-time application logs and diagnostics
            </p>
          </div>
          
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`btn-secondary flex items-center ${autoRefresh ? 'bg-primary-100 dark:bg-primary-900/30' : ''}`}
          >
            <ArrowPathIcon className={`h-5 w-5 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto-refreshing' : 'Auto-refresh'}
          </button>
        </div>

        {error ? (
          <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
            <p className="text-sm text-yellow-800 dark:text-yellow-300">{error}</p>
          </div>
        ) : (
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Search Filter */}
            <div className="flex-1">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Filter logs..."
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  className="input-primary pl-10"
                />
                <FunnelIcon className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              </div>
            </div>

            {/* Level Filter */}
            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="input-primary"
            >
              <option value="all">All Levels</option>
              <option value="error">Error</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
              <option value="debug">Debug</option>
            </select>

            {/* Lines Selector */}
            <select
              value={lines}
              onChange={(e) => setLines(Number(e.target.value))}
              className="input-primary"
            >
              <option value="50">Last 50 lines</option>
              <option value="100">Last 100 lines</option>
              <option value="200">Last 200 lines</option>
              <option value="500">Last 500 lines</option>
            </select>
          </div>
        )}
      </div>

      {/* Logs Display */}
      {!error && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Showing {filteredLogs.length} of {logs.length} log entries
            </p>
          </div>
          
          <div className="p-4 font-mono text-sm max-h-[600px] overflow-y-auto">
            {filteredLogs.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                No logs match the current filter
              </p>
            ) : (
              <div className="space-y-2">
                {filteredLogs.map((log, index) => (
                  <div
                    key={index}
                    className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 py-2 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors"
                  >
                    {log.timestamp && log.level && log.message ? (
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs text-gray-500 dark:text-gray-400">
                            {new Date(log.timestamp).toLocaleTimeString()}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${getLogLevelColor(log.level)}`}>
                            {log.level}
                          </span>
                          {log.logger && (
                            <span className="text-xs text-gray-600 dark:text-gray-400">
                              [{log.logger}]
                            </span>
                          )}
                        </div>
                        <div className="text-gray-700 dark:text-gray-300 break-all">
                          {log.message}
                        </div>
                      </div>
                    ) : (
                      <div className="text-gray-700 dark:text-gray-300 break-all">
                        {log.raw || JSON.stringify(log)}
                      </div>
                    )}
                  </div>
                ))}
                <div ref={logsEndRef} />
              </div>
            )}
          </div>
          
          {filteredLogs.length > 20 && (
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={scrollToBottom}
                className="text-sm text-primary-600 dark:text-primary-400 hover:underline"
              >
                Scroll to bottom ↓
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}