import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { agentAPI } from '../../services/api';
import {
  CpuChipIcon,
  SparklesIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  PlayIcon,
  StopIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { motion } from 'framer-motion';

const AgentStatus: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedAgent, setSelectedAgent] = useState<any>(null);

  const { data: agents, isLoading, refetch } = useQuery(
    'agents',
    agentAPI.getAgents,
    { refetchInterval: 3000 }
  );

  const resetMutation = useMutation(agentAPI.resetAgents, {
    onSuccess: () => {
      toast.success('All agents reset successfully');
      queryClient.invalidateQueries('agents');
    },
    onError: () => {
      toast.error('Failed to reset agents');
    },
  });

  const getAgentIcon = (role: string) => {
    switch (role) {
      case 'manager':
        return <SparklesIcon className="h-6 w-6" />;
      case 'bing_search':
        return <MagnifyingGlassIcon className="h-6 w-6" />;
      case 'ai_search':
        return <CpuChipIcon className="h-6 w-6" />;
      default:
        return <CpuChipIcon className="h-6 w-6" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'idle':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'processing':
        return <ArrowPathIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getAgentColor = (role: string) => {
    switch (role) {
      case 'manager':
        return 'from-purple-500 to-purple-600';
      case 'bing_search':
        return 'from-green-500 to-green-600';
      case 'ai_search':
        return 'from-orange-500 to-orange-600';
      default:
        return 'from-gray-500 to-gray-600';
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'idle':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'processing':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Agent Management
            </h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Monitor and control AI research agents
            </p>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => refetch()}
              className="btn-outline flex items-center space-x-2"
              disabled={isLoading}
            >
              <ArrowPathIcon className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
            <button
              onClick={() => resetMutation.mutate()}
              className="btn-secondary flex items-center space-x-2"
              disabled={resetMutation.isLoading}
            >
              <ArrowPathIcon className={`h-5 w-5 ${resetMutation.isLoading ? 'animate-spin' : ''}`} />
              <span>Reset All</span>
            </button>
          </div>
        </div>
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents?.map((agent: any) => (
          <motion.div
            key={agent.id}
            whileHover={{ scale: 1.02 }}
            onClick={() => setSelectedAgent(agent)}
            className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 cursor-pointer hover:shadow-md transition-shadow"
          >
            {/* Agent Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className={`p-3 rounded-lg bg-gradient-to-r ${getAgentColor(agent.role)} text-white`}>
                  {getAgentIcon(agent.role)}
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {agent.name}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                    {agent.role.replace('_', ' ')}
                  </p>
                </div>
              </div>
              {getStatusIcon(agent.status)}
            </div>

            {/* Status Badge */}
            <div className="mb-4">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(agent.status)}`}>
                {agent.status.toUpperCase()}
              </span>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500 dark:text-gray-400">Total Requests</p>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {agent.metrics?.total_requests || 0}
                </p>
              </div>
              <div>
                <p className="text-gray-500 dark:text-gray-400">Success Rate</p>
                <p className="font-semibold text-gray-900 dark:text-white">
                  {agent.metrics?.success_rate ? `${(agent.metrics.success_rate * 100).toFixed(1)}%` : 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-gray-500 dark:text-gray-400">Successful</p>
                <p className="font-semibold text-green-600 dark:text-green-400">
                  {agent.metrics?.successful_requests || 0}
                </p>
              </div>
              <div>
                <p className="text-gray-500 dark:text-gray-400">Failed</p>
                <p className="font-semibold text-red-600 dark:text-red-400">
                  {agent.metrics?.failed_requests || 0}
                </p>
              </div>
            </div>

            {/* Current Metrics */}
            {agent.metrics?.current_metrics && (
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                  Current Session
                </p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {agent.metrics.current_metrics.processing_time_ms && (
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Last Response:</span>
                      <span className="ml-1 font-medium text-gray-900 dark:text-white">
                        {Math.round(agent.metrics.current_metrics.processing_time_ms)}ms
                      </span>
                    </div>
                  )}
                  {agent.metrics.current_metrics.tokens_used > 0 && (
                    <div>
                      <span className="text-gray-500 dark:text-gray-400">Tokens:</span>
                      <span className="ml-1 font-medium text-gray-900 dark:text-white">
                        {agent.metrics.current_metrics.tokens_used}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* Selected Agent Details */}
      {selectedAgent && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Agent Details: {selectedAgent.name}
            </h2>
            <button
              onClick={() => setSelectedAgent(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              <XCircleIcon className="h-5 w-5" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Configuration
              </h3>
              <dl className="space-y-2">
                <div>
                  <dt className="text-xs text-gray-500 dark:text-gray-400">Agent ID</dt>
                  <dd className="text-sm font-mono text-gray-900 dark:text-white">
                    {selectedAgent.id}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500 dark:text-gray-400">Role</dt>
                  <dd className="text-sm text-gray-900 dark:text-white capitalize">
                    {selectedAgent.role.replace('_', ' ')}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500 dark:text-gray-400">Status</dt>
                  <dd className="text-sm text-gray-900 dark:text-white capitalize">
                    {selectedAgent.status}
                  </dd>
                </div>
              </dl>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Performance Metrics
              </h3>
              <dl className="space-y-2">
                <div>
                  <dt className="text-xs text-gray-500 dark:text-gray-400">Total Requests</dt>
                  <dd className="text-sm text-gray-900 dark:text-white">
                    {selectedAgent.metrics?.total_requests || 0}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500 dark:text-gray-400">Success Rate</dt>
                  <dd className="text-sm text-gray-900 dark:text-white">
                    {selectedAgent.metrics?.success_rate 
                      ? `${(selectedAgent.metrics.success_rate * 100).toFixed(2)}%` 
                      : 'N/A'}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-gray-500 dark:text-gray-400">
                    Avg Processing Time
                  </dt>
                  <dd className="text-sm text-gray-900 dark:text-white">
                    {selectedAgent.metrics?.current_metrics?.processing_time_ms
                      ? `${Math.round(selectedAgent.metrics.current_metrics.processing_time_ms)}ms`
                      : 'N/A'}
                  </dd>
                </div>
              </dl>
            </div>
          </div>

          {/* Actions */}
          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 flex space-x-2">
            <button className="btn-outline flex items-center space-x-2">
              <PlayIcon className="h-4 w-4" />
              <span>Start</span>
            </button>
            <button className="btn-outline flex items-center space-x-2">
              <StopIcon className="h-4 w-4" />
              <span>Stop</span>
            </button>
            <button className="btn-outline flex items-center space-x-2">
              <ArrowPathIcon className="h-4 w-4" />
              <span>Restart</span>
            </button>
          </div>
        </div>
      )}

      {/* Agent Summary */}
      {agents && agents.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            System Summary
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {agents.length}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Agents</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {agents.filter((a: any) => a.status === 'idle' || a.status === 'completed').length}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Ready</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {agents.filter((a: any) => a.status === 'processing').length}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Processing</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                {agents.filter((a: any) => a.status === 'failed').length}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Failed</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentStatus;