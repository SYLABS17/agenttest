import React, { useEffect, useState } from 'react';
import { useQuery } from 'react-query';
import { metricsAPI } from '../../services/api';
import {
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const ObservabilityPanel: React.FC = () => {
  const { data: metrics, isLoading, refetch } = useQuery(
    'metrics',
    metricsAPI.getMetrics,
    { refetchInterval: 5000 }
  );

  const { data: evaluations } = useQuery(
    'evaluations',
    () => metricsAPI.getEvaluationHistory(20),
    { refetchInterval: 10000 }
  );

  // Mock data for charts (in production, this would come from real metrics)
  const latencyData = [
    { time: '00:00', value: 1200 },
    { time: '04:00', value: 980 },
    { time: '08:00', value: 1500 },
    { time: '12:00', value: 2100 },
    { time: '16:00', value: 1800 },
    { time: '20:00', value: 1400 },
    { time: '24:00', value: 1100 },
  ];

  const agentPerformance = metrics?.agent_metrics || [];
  
  const pieData = [
    { name: 'Successful', value: metrics?.evaluation_summary?.average_score ? metrics.evaluation_summary.average_score * 100 : 70, color: '#10b981' },
    { name: 'Failed', value: 100 - (metrics?.evaluation_summary?.average_score ? metrics.evaluation_summary.average_score * 100 : 70), color: '#ef4444' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Observability & Monitoring
            </h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Real-time system metrics and performance monitoring
            </p>
          </div>
          <button
            onClick={() => refetch()}
            className="p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
            disabled={isLoading}
          >
            <ArrowPathIcon className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Avg Latency"
          value={metrics?.observability_metrics?.request_latency?.avg ? 
            `${Math.round(metrics.observability_metrics.request_latency.avg)}ms` : 'N/A'}
          icon={ClockIcon}
          trend="neutral"
        />
        <MetricCard
          title="Total Requests"
          value={metrics?.observability_metrics?.request_count?.count?.toString() || '0'}
          icon={ChartBarIcon}
          trend="up"
        />
        <MetricCard
          title="Success Rate"
          value={`${Math.round((metrics?.evaluation_summary?.average_score || 0) * 100)}%`}
          icon={CheckCircleIcon}
          trend={metrics?.evaluation_summary?.average_score > 0.7 ? 'up' : 'down'}
        />
        <MetricCard
          title="Error Rate"
          value={`${Math.round((metrics?.observability_metrics?.error_count?.count || 0) / 
            (metrics?.observability_metrics?.request_count?.count || 1) * 100)}%`}
          icon={ExclamationTriangleIcon}
          trend="neutral"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Latency Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Response Latency (24h)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={latencyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: 'none',
                  borderRadius: '8px',
                }}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: '#3b82f6' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Success Rate Pie Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Request Success Rate
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${entry.value.toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Agent Performance */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Agent Performance Metrics
        </h3>
        {agentPerformance.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Agent
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Requests
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Success Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {agentPerformance.map((agent: any) => (
                  <tr key={agent.agent_id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {agent.agent_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {agent.role}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {agent.total_requests}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {(agent.success_rate * 100).toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 text-xs font-semibold rounded-full
                        ${agent.status === 'idle' ? 'bg-green-100 text-green-800' : ''}
                        ${agent.status === 'processing' ? 'bg-blue-100 text-blue-800' : ''}
                        ${agent.status === 'failed' ? 'bg-red-100 text-red-800' : ''}
                      `}>
                        {agent.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400">No agent performance data available</p>
        )}
      </div>

      {/* Recent Evaluations */}
      {evaluations?.evaluations && evaluations.evaluations.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Recent Evaluations
          </h3>
          <div className="space-y-3">
            {evaluations.evaluations.slice(0, 5).map((eval: any, index: number) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {eval.query}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {new Date(eval.timestamp).toLocaleString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">
                    {(eval.overall_score * 100).toFixed(0)}%
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {eval.quality_assessment}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

interface MetricCardProps {
  title: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  trend: 'up' | 'down' | 'neutral';
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, icon: Icon, trend }) => {
  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-2">
        <Icon className="h-8 w-8 text-gray-400" />
        <span className={`text-sm font-medium ${getTrendColor()}`}>
          {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
        </span>
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{title}</p>
    </div>
  );
};

export default ObservabilityPanel;