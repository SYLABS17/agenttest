import React from 'react';
import { Link } from 'react-router-dom';
import {
  SparklesIcon,
  MagnifyingGlassIcon,
  CpuChipIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';

interface Agent {
  id: string;
  name: string;
  role: string;
  status: string;
  metrics: any;
}

interface AgentStatusCardProps {
  agents: Agent[];
}

const AgentStatusCard: React.FC<AgentStatusCardProps> = ({ agents }) => {
  const getAgentIcon = (role: string) => {
    switch (role) {
      case 'manager':
        return <SparklesIcon className="h-5 w-5" />;
      case 'bing_search':
        return <MagnifyingGlassIcon className="h-5 w-5" />;
      case 'ai_search':
        return <CpuChipIcon className="h-5 w-5" />;
      default:
        return <CpuChipIcon className="h-5 w-5" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'idle':
        return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
      case 'processing':
        return <ArrowPathIcon className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircleIcon className="h-4 w-4 text-red-500" />;
      default:
        return <ClockIcon className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'idle':
        return 'Ready';
      case 'processing':
        return 'Processing';
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      default:
        return 'Unknown';
    }
  };

  const getAgentColor = (role: string) => {
    switch (role) {
      case 'manager':
        return 'bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400';
      case 'bing_search':
        return 'bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-400';
      case 'ai_search':
        return 'bg-orange-50 text-orange-600 dark:bg-orange-900/20 dark:text-orange-400';
      default:
        return 'bg-gray-50 text-gray-600 dark:bg-gray-900/20 dark:text-gray-400';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Agent Status
        </h2>
        <Link to="/agents">
          <button className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300">
            Manage
          </button>
        </Link>
      </div>

      <div className="space-y-3">
        {agents.length === 0 ? (
          <div className="text-center py-8">
            <CpuChipIcon className="h-10 w-10 text-gray-400 mx-auto mb-3" />
            <p className="text-sm text-gray-500 dark:text-gray-400">
              No agents available
            </p>
          </div>
        ) : (
          agents.map((agent, index) => (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${getAgentColor(agent.role)}`}>
                    {getAgentIcon(agent.role)}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {agent.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {agent.metrics?.total_requests || 0} requests
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-1">
                  {getStatusIcon(agent.status)}
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {getStatusText(agent.status)}
                  </span>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>

      {agents.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500 dark:text-gray-400">Total Agents</p>
              <p className="font-semibold text-gray-900 dark:text-white">
                {agents.length}
              </p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400">Active</p>
              <p className="font-semibold text-gray-900 dark:text-white">
                {agents.filter(a => a.status === 'idle' || a.status === 'processing').length}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentStatusCard;