import React from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { DocumentTextIcon, ClockIcon } from '@heroicons/react/24/outline';
import { useResearchStore } from '../../stores/researchStore';
import { motion } from 'framer-motion';

const RecentReports: React.FC = () => {
  const { reports, setCurrentReport } = useResearchStore();
  const recentReports = reports.slice(0, 5);

  const getScoreBadgeColor = (score: number) => {
    if (score >= 0.8) return 'badge-success';
    if (score >= 0.6) return 'badge-warning';
    return 'badge-error';
  };

  if (recentReports.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Recent Reports
        </h2>
        <div className="text-center py-12">
          <DocumentTextIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-gray-400">
            No reports generated yet
          </p>
          <Link to="/chat">
            <button className="mt-4 btn-primary">
              Start Research
            </button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Recent Reports
        </h2>
        <Link to="/reports">
          <button className="text-sm text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300">
            View all
          </button>
        </Link>
      </div>
      
      <div className="space-y-3">
        {recentReports.map((report, index) => (
          <motion.div
            key={report.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Link
              to="/reports"
              onClick={() => setCurrentReport(report)}
              className="block p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {report.query}
                  </p>
                  <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                    <span className="flex items-center">
                      <ClockIcon className="h-3 w-3 mr-1" />
                      {format(report.timestamp, 'MMM d, HH:mm')}
                    </span>
                    {report.processingTime && (
                      <span>
                        {Math.round(report.processingTime)}ms
                      </span>
                    )}
                    {report.evaluation && (
                      <span className={`badge ${getScoreBadgeColor(report.evaluation.overall_score)}`}>
                        {Math.round(report.evaluation.overall_score * 100)}%
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default RecentReports;