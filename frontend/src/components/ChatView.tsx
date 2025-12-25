import { formatDistanceToNow } from 'date-fns'
import { UserIcon, CpuChipIcon, BeakerIcon, MagnifyingGlassIcon, BookOpenIcon } from '@heroicons/react/24/outline'
import { ChatMessage } from '../services/api'

interface ChatViewProps {
  messages: ChatMessage[]
}

export default function ChatView({ messages }: ChatViewProps) {
  const getAgentIcon = (agentName: string) => {
    switch (agentName) {
      case 'ManagerAgent':
        return <CpuChipIcon className="h-5 w-5" />
      case 'BingSearchAgent':
        return <MagnifyingGlassIcon className="h-5 w-5" />
      case 'AISearchAgent':
        return <BookOpenIcon className="h-5 w-5" />
      default:
        return <BeakerIcon className="h-5 w-5" />
    }
  }

  const getAgentColor = (agentName: string) => {
    switch (agentName) {
      case 'ManagerAgent':
        return 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300'
      case 'BingSearchAgent':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300'
      case 'AISearchAgent':
        return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
      default:
        return 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300'
    }
  }

  const formatContent = (content: string) => {
    // Convert markdown-style formatting to HTML
    return content
      .split('\n')
      .map((line, i) => {
        // Handle headers
        if (line.startsWith('### ')) {
          return <h3 key={i} className="text-lg font-semibold mt-4 mb-2">{line.replace('### ', '')}</h3>
        }
        if (line.startsWith('## ')) {
          return <h2 key={i} className="text-xl font-bold mt-4 mb-2">{line.replace('## ', '')}</h2>
        }
        if (line.startsWith('# ')) {
          return <h1 key={i} className="text-2xl font-bold mt-4 mb-2">{line.replace('# ', '')}</h1>
        }
        
        // Handle bullet points
        if (line.startsWith('- ') || line.startsWith('* ')) {
          return (
            <li key={i} className="ml-4 list-disc">
              {line.replace(/^[*-]\s/, '')}
            </li>
          )
        }
        
        // Handle numbered lists
        const numberedMatch = line.match(/^(\d+)\.\s(.+)/)
        if (numberedMatch) {
          return (
            <li key={i} className="ml-4 list-decimal">
              {numberedMatch[2]}
            </li>
          )
        }
        
        // Handle bold text
        let formattedLine = line
        const boldRegex = /\*\*(.+?)\*\*/g
        const boldMatches = [...line.matchAll(boldRegex)]
        if (boldMatches.length > 0) {
          const parts = []
          let lastIndex = 0
          
          boldMatches.forEach((match, idx) => {
            if (match.index !== undefined) {
              parts.push(
                <span key={`text-${idx}`}>{line.slice(lastIndex, match.index)}</span>
              )
              parts.push(
                <strong key={`bold-${idx}`}>{match[1]}</strong>
              )
              lastIndex = match.index + match[0].length
            }
          })
          
          if (lastIndex < line.length) {
            parts.push(<span key="text-last">{line.slice(lastIndex)}</span>)
          }
          
          return <p key={i} className="mb-2">{parts}</p>
        }
        
        // Regular paragraph
        if (line.trim()) {
          return <p key={i} className="mb-2">{line}</p>
        }
        
        // Empty line
        return <br key={i} />
      })
  }

  return (
    <div className="space-y-4 max-h-[600px] overflow-y-auto scrollbar-thin">
      {messages.map((message, index) => (
        <div
          key={message.id || index}
          className="flex items-start space-x-3 animate-fade-in"
          style={{ animationDelay: `${index * 50}ms` }}
        >
          {/* Agent Avatar */}
          <div className={`flex-shrink-0 p-2 rounded-full ${getAgentColor(message.agent_name)}`}>
            {getAgentIcon(message.agent_name)}
          </div>
          
          {/* Message Content */}
          <div className="flex-1 bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium text-gray-900 dark:text-white">
                {message.agent_name}
              </h4>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {message.timestamp ? formatDistanceToNow(new Date(message.timestamp), { addSuffix: true }) : 'just now'}
              </span>
            </div>
            
            <div className="text-sm text-gray-700 dark:text-gray-300 prose dark:prose-invert max-w-none">
              {formatContent(message.content)}
            </div>
            
            {/* Metadata Display */}
            {message.metadata && Object.keys(message.metadata).length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                <div className="flex flex-wrap gap-2">
                  {message.metadata.latency_ms && (
                    <span className="badge badge-info">
                      Latency: {message.metadata.latency_ms.toFixed(0)}ms
                    </span>
                  )}
                  {message.metadata.result_count !== undefined && (
                    <span className="badge badge-success">
                      Results: {message.metadata.result_count}
                    </span>
                  )}
                  {message.metadata.phase && (
                    <span className="badge badge-warning">
                      Phase: {message.metadata.phase}
                    </span>
                  )}
                  {message.metadata.search_type && (
                    <span className="badge badge-info">
                      Type: {message.metadata.search_type}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}