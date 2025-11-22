import React from 'react';
import { motion } from 'framer-motion';
import { ArrowUpIcon, ArrowDownIcon, MinusIcon } from '@heroicons/react/24/outline';

interface MetricsCardProps {
  title: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  trend: 'up' | 'down' | 'neutral';
  trendValue: string;
  color: 'blue' | 'green' | 'yellow' | 'purple' | 'red';
}

const MetricsCard: React.FC<MetricsCardProps> = ({
  title,
  value,
  icon: Icon,
  trend,
  trendValue,
  color,
}) => {
  const getColorClasses = () => {
    const colors = {
      blue: 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400',
      green: 'bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-400',
      yellow: 'bg-yellow-50 text-yellow-600 dark:bg-yellow-900/20 dark:text-yellow-400',
      purple: 'bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400',
      red: 'bg-red-50 text-red-600 dark:bg-red-900/20 dark:text-red-400',
    };
    return colors[color];
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <ArrowUpIcon className="h-4 w-4 text-green-500" />;
      case 'down':
        return <ArrowDownIcon className="h-4 w-4 text-red-500" />;
      default:
        return <MinusIcon className="h-4 w-4 text-gray-400" />;
    }
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`p-2 rounded-lg ${getColorClasses()}`}>
          <Icon className="h-6 w-6" />
        </div>
        <div className="flex items-center space-x-1">
          {getTrendIcon()}
          <span className="text-sm text-gray-500 dark:text-gray-400">
            {trendValue}
          </span>
        </div>
      </div>
      
      <div>
        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">
          {title}
        </h3>
        <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-white">
          {value}
        </p>
      </div>
    </motion.div>
  );
};

export default MetricsCard;