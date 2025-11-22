import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PaperAirplaneIcon,
  SparklesIcon,
  MagnifyingGlassIcon,
  CpuChipIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { useResearchStore } from '../../stores/researchStore';
import { researchAPI } from '../../services/api';
import toast from 'react-hot-toast';
import MessageBubble from './MessageBubble';
import QuerySuggestions from './QuerySuggestions';

const ChatInterface: React.FC = () => {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  const {
    messages,
    addMessage,
    clearMessages,
    setIsResearching,
    setCurrentQuery,
    addReport,
  } = useResearchStore();

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const query = input.trim();
    setInput('');
    setIsLoading(true);
    setIsResearching(true);
    setCurrentQuery(query);

    // Add user message
    addMessage({
      role: 'user',
      content: query,
    });

    try {
      // Add system message
      addMessage({
        role: 'system',
        content: 'Initiating multi-agent research...',
      });

      // Conduct research
      const response = await researchAPI.conductResearch(query);

      // Add agent responses (simulated)
      if (response.report) {
        // Manager agent message
        addMessage({
          role: 'manager',
          content: 'Coordinating research across multiple agents...',
        });

        // Bing Search agent message
        addMessage({
          role: 'bing_search',
          content: 'Searching web sources for relevant information...',
        });

        // AI Search agent message
        addMessage({
          role: 'ai_search',
          content: 'Querying internal knowledge base...',
        });

        // Final report message
        addMessage({
          role: 'manager',
          content: `Research completed! Here's your comprehensive report:\n\n${response.report.executive_summary || response.report.title || 'Report generated successfully.'}`,
          metadata: response.report,
        });

        // Add report to store
        addReport({
          id: response.request_id,
          query: query,
          report: response.report,
          evaluation: response.evaluation,
          timestamp: new Date(),
          processingTime: response.processing_time_ms,
        });

        toast.success('Research completed successfully!');
      }
    } catch (error: any) {
      console.error('Research error:', error);
      addMessage({
        role: 'system',
        content: `Error: ${error.response?.data?.detail || error.message || 'Failed to complete research'}`,
      });
      toast.error('Failed to complete research');
    } finally {
      setIsLoading(false);
      setIsResearching(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion);
    inputRef.current?.focus();
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-t-xl shadow-sm border border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Research Chat
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Ask questions and get AI-powered research insights
            </p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="flex items-center text-sm text-gray-500 dark:text-gray-400">
              <span className="w-2 h-2 bg-green-400 rounded-full mr-2 animate-pulse"></span>
              3 agents ready
            </span>
            <button
              onClick={clearMessages}
              className="p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
              aria-label="Clear chat"
            >
              <ArrowPathIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 bg-gray-50 dark:bg-gray-900 overflow-y-auto">
        <div className="p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-12">
              <div className="w-16 h-16 bg-gradient-to-r from-primary-500 to-primary-600 rounded-full flex items-center justify-center mb-4">
                <SparklesIcon className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Start Your Research
              </h3>
              <p className="text-gray-500 dark:text-gray-400 max-w-md mb-6">
                Type your research question below, and our AI agents will collaborate to provide comprehensive insights.
              </p>
              <QuerySuggestions onSuggestionClick={handleSuggestionClick} />
            </div>
          ) : (
            <>
              <AnimatePresence>
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{ duration: 0.3 }}
                  >
                    <MessageBubble message={message} />
                  </motion.div>
                ))}
              </AnimatePresence>
              {isLoading && (
                <div className="flex items-center space-x-2 text-gray-500 dark:text-gray-400">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                  <span className="text-sm">Researching...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white dark:bg-gray-800 rounded-b-xl shadow-lg border-t border-gray-200 dark:border-gray-700 px-6 py-4">
        <form onSubmit={handleSubmit} className="flex items-end space-x-4">
          <div className="flex-1">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask your research question..."
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 resize-none"
              rows={2}
              disabled={isLoading}
            />
          </div>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="submit"
            disabled={!input.trim() || isLoading}
            className="btn-primary flex items-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <PaperAirplaneIcon className="h-5 w-5" />
            <span>Research</span>
          </motion.button>
        </form>
        <div className="mt-3 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>Press Enter to send, Shift+Enter for new line</span>
          <span>{input.length}/1000 characters</span>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;