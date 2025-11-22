import React from 'react';
import { format } from 'date-fns';
import {
  UserIcon,
  CpuChipIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline';
import { Message } from '../../stores/researchStore';

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const getRoleIcon = () => {
    switch (message.role) {
      case 'user':
        return <UserIcon className="h-5 w-5" />;
      case 'manager':
        return <SparklesIcon className="h-5 w-5" />;
      case 'bing_search':
        return <MagnifyingGlassIcon className="h-5 w-5" />;
      case 'ai_search':
        return <CpuChipIcon className="h-5 w-5" />;
      case 'system':
        return <ExclamationCircleIcon className="h-5 w-5" />;
      default:
        return <CpuChipIcon className="h-5 w-5" />;
    }
  };

  const getRoleColor = () => {
    switch (message.role) {
      case 'user':
        return 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400';
      case 'manager':
        return 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400';
      case 'bing_search':
        return 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400';
      case 'ai_search':
        return 'bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400';
      case 'system':
        return 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400';
      default:
        return 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400';
    }
  };

  const getRoleName = () => {
    switch (message.role) {
      case 'user':
        return 'You';
      case 'manager':
        return 'Manager Agent';
      case 'bing_search':
        return 'Bing Search Agent';
      case 'ai_search':
        return 'AI Search Agent';
      case 'system':
        return 'System';
      default:
        return 'Agent';
    }
  };

  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-3xl ${isUser ? 'order-2' : ''}`}>
        <div className={`flex items-start space-x-3 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
          {/* Avatar */}
          <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${getRoleColor()}`}>
            {getRoleIcon()}
          </div>
          
          {/* Message Content */}
          <div className="flex-1">
            <div className={`flex items-baseline space-x-2 mb-1 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                {getRoleName()}
              </span>
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {format(message.timestamp, 'HH:mm:ss')}
              </span>
            </div>
            
            <div
              className={`
                rounded-lg px-4 py-3
                ${isUser 
                  ? 'bg-primary-600 text-white' 
                  : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border border-gray-200 dark:border-gray-700'
                }
              `}
            >
              <div className="whitespace-pre-wrap break-words">
                {message.content}
              </div>
              
              {/* Metadata (for reports) */}
              {message.metadata && message.role === 'manager' && message.metadata.title && (
                <div className="mt-3 pt-3 border-t border-white/20">
                  <div className="text-sm opacity-90">
                    <p className="font-semibold mb-2">📊 Research Report Available</p>
                    <p className="text-xs">View the full report in the Reports section for detailed analysis, recommendations, and sources.</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;