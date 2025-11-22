import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  ChartBarIcon,
  DocumentTextIcon,
  CpuChipIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { useQuery } from 'react-query';
import { systemAPI, metricsAPI, agentAPI } from '../../services/api';
import { useResearchStore } from '../../stores/researchStore';
import { Link } from 'react-router-dom';
import MetricsCard from './MetricsCard';
import RecentReports from './RecentReports';
import AgentStatusCard from './AgentStatusCard';

const ResearchDashboard: React.FC = () => {
  const { reports } = useResearchStore();
  
  // Fetch health status
  const { data: healthData } = useQuery(
    'health',
    systemAPI.healthCheck,
    { refetchInterval: 30000 }
  );
  
  // Fetch metrics
  const { data: metricsData } = useQuery(
    'metrics',
    metricsAPI.getMetrics,
    { refetchInterval: 10000 }
  );
  
  // Fetch agents
  const { data: agentsData } = useQuery(
    'agents',
    agentAPI.getAgents,
    { refetchInterval: 5000 }
  );

  const getSystemStatus = () => {
    if (!healthData) return 'unknown';
    return healthData.status;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100';
      case 'unhealthy':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Research Dashboard
            </h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Monitor your AI research system performance and activity
            </p>
          </div>
          <div className="mt-4 md:mt-0">
            <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(getSystemStatus())}`}>
              {getSystemStatus() === 'healthy' ? (
                <CheckCircleIcon className="h-4 w-4 mr-2" />
              ) : (
                <ExclamationTriangleIcon className="h-4 w-4 mr-2" />
              )}
              System {getSystemStatus()}
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricsCard
          title="Total Reports"
          value={reports.length.toString()}
          icon={DocumentTextIcon}
          trend={reports.length > 0 ? 'up' : 'neutral'}
          trendValue={reports.length > 0 ? '+100%' : '0%'}
          color="blue"
        />
        
        <MetricsCard
          title="Active Agents"
          value={agentsData?.length.toString() || '0'}
          icon={CpuChipIcon}
          trend="neutral"
          trendValue={`${agentsData?.length || 0} online`}
          color="green"
        />
        
        <MetricsCard
          title="Avg Response Time"
          value={
            metricsData?.observability_metrics?.request_latency?.avg
              ? `${Math.round(metricsData.observability_metrics.request_latency.avg)}ms`
              : 'N/A'
          }
          icon={ClockIcon}
          trend="neutral"
          trendValue="Last 24h"
          color="yellow"
        />
        
        <MetricsCard
          title="Success Rate"
          value={
            metricsData?.evaluation_summary?.average_score
              ? `${Math.round(metricsData.evaluation_summary.average_score * 100)}%`
              : 'N/A'
          }
          icon={ChartBarIcon}
          trend={
            metricsData?.evaluation_summary?.average_score > 0.7
              ? 'up'
              : metricsData?.evaluation_summary?.average_score > 0.5
              ? 'neutral'
              : 'down'
          }
          trendValue="Performance"
          color="purple"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Reports - Takes 2 columns */}
        <div className="lg:col-span-2">
          <RecentReports />
        </div>
        
        {/* Agent Status */}
        <div>
          <AgentStatusCard agents={agentsData || []} />
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link to="/chat">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full btn-outline flex items-center justify-center space-x-2"
            >
              <ChartBarIcon className="h-5 w-5" />
              <span>New Research</span>
            </motion.button>
          </Link>
          
          <Link to="/reports">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full btn-outline flex items-center justify-center space-x-2"
            >
              <DocumentTextIcon className="h-5 w-5" />
              <span>View Reports</span>
            </motion.button>
          </Link>
          
          <Link to="/agents">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full btn-outline flex items-center justify-center space-x-2"
            >
              <CpuChipIcon className="h-5 w-5" />
              <span>Manage Agents</span>
            </motion.button>
          </Link>
          
          <Link to="/observability">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full btn-outline flex items-center justify-center space-x-2"
            >
              <ChartBarIcon className="h-5 w-5" />
              <span>View Metrics</span>
            </motion.button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ResearchDashboard;