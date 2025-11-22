import { useState } from 'react'
import { MagnifyingGlassIcon, DocumentTextIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline'
import { apiService, ResearchResponse, ChatMessage } from '../services/api'
import ChatView from '../components/ChatView'
import ReportView from '../components/ReportView'
import EvaluationView from '../components/EvaluationView'
import LoadingSpinner from '../components/LoadingSpinner'

const SAMPLE_QUERIES = [
  "Future of renewable energy in Africa",
  "Impact of generative AI on journalism",
  "Quantum computing applications in healthcare",
  "Sustainable urban development strategies",
  "Blockchain in supply chain management",
]

export default function ResearchPage() {
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [response, setResponse] = useState<ResearchResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'chat' | 'report' | 'evaluation'>('chat')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setIsLoading(true)
    setError(null)
    setResponse(null)

    try {
      const result = await apiService.conductResearch({
        query: query.trim(),
        include_evaluation: true,
      })
      setResponse(result)
      if (result.report) {
        setActiveTab('report')
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSampleQuery = (sampleQuery: string) => {
    setQuery(sampleQuery)
  }

  const handleTestQuery = async () => {
    setIsLoading(true)
    setError(null)
    setResponse(null)

    try {
      const result = await apiService.testDummyQuery()
      setResponse(result)
      setQuery(result.query)
      if (result.report) {
        setActiveTab('report')
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Search Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
          AI Research Assistant
        </h1>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Enter your research query
            </label>
            <div className="relative">
              <input
                type="text"
                id="query"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., Future of renewable energy in Africa"
                className="input-primary pl-10 pr-4 py-3 text-base"
                disabled={isLoading}
              />
              <MagnifyingGlassIcon className="absolute left-3 top-3.5 h-5 w-5 text-gray-400" />
            </div>
          </div>

          {/* Sample Queries */}
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Try a sample query:</p>
            <div className="flex flex-wrap gap-2">
              {SAMPLE_QUERIES.map((sample) => (
                <button
                  key={sample}
                  type="button"
                  onClick={() => handleSampleQuery(sample)}
                  className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200"
                  disabled={isLoading}
                >
                  {sample}
                </button>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <button
              type="submit"
              disabled={isLoading || !query.trim()}
              className="btn-primary flex items-center"
            >
              {isLoading ? (
                <>
                  <LoadingSpinner size="sm" className="mr-2" />
                  Researching...
                </>
              ) : (
                <>
                  <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
                  Start Research
                </>
              )}
            </button>
            
            <button
              type="button"
              onClick={handleTestQuery}
              disabled={isLoading}
              className="btn-secondary"
            >
              Test with Dummy Query
            </button>
          </div>
        </form>

        {/* Error Display */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-sm text-red-800 dark:text-red-300">{error}</p>
          </div>
        )}
      </div>

      {/* Results Section */}
      {response && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md">
          {/* Tabs */}
          <div className="border-b border-gray-200 dark:border-gray-700">
            <nav className="flex -mb-px">
              <button
                onClick={() => setActiveTab('chat')}
                className={`
                  px-6 py-3 border-b-2 font-medium text-sm transition-colors duration-200
                  ${activeTab === 'chat'
                    ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                  }
                `}
              >
                <ChatBubbleLeftRightIcon className="h-5 w-5 inline-block mr-2" />
                Agent Chat ({response.chat_history?.length || 0})
              </button>
              
              <button
                onClick={() => setActiveTab('report')}
                className={`
                  px-6 py-3 border-b-2 font-medium text-sm transition-colors duration-200
                  ${activeTab === 'report'
                    ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                  }
                `}
              >
                <DocumentTextIcon className="h-5 w-5 inline-block mr-2" />
                Research Report
              </button>
              
              {response.evaluation && (
                <button
                  onClick={() => setActiveTab('evaluation')}
                  className={`
                    px-6 py-3 border-b-2 font-medium text-sm transition-colors duration-200
                    ${activeTab === 'evaluation'
                      ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
                    }
                  `}
                >
                  Evaluation
                </button>
              )}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'chat' && response.chat_history && (
              <ChatView messages={response.chat_history} />
            )}
            
            {activeTab === 'report' && response.report && (
              <ReportView report={response.report} />
            )}
            
            {activeTab === 'evaluation' && response.evaluation && (
              <EvaluationView evaluation={response.evaluation} />
            )}
          </div>

          {/* Processing Time */}
          <div className="border-t border-gray-200 dark:border-gray-700 px-6 py-3">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Processing time: {response.processing_time_ms.toFixed(0)}ms
            </p>
          </div>
        </div>
      )}
    </div>
  )
}