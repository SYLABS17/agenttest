import React, { useState } from 'react';
import { format } from 'date-fns';
import {
  DocumentTextIcon,
  ChevronDownIcon,
  ChevronRightIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  DocumentDuplicateIcon,
  ArrowDownTrayIcon,
} from '@heroicons/react/24/outline';
import { useResearchStore } from '../../stores/researchStore';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

const ReportViewer: React.FC = () => {
  const { reports, currentReport, setCurrentReport } = useResearchStore();
  const [expandedSections, setExpandedSections] = useState<string[]>(['summary']);

  const toggleSection = (section: string) => {
    setExpandedSections(prev =>
      prev.includes(section)
        ? prev.filter(s => s !== section)
        : [...prev, section]
    );
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const downloadReport = (report: any) => {
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `report-${report.id || Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('Report downloaded!');
  };

  if (reports.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-12 text-center">
        <DocumentTextIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          No Reports Available
        </h2>
        <p className="text-gray-500 dark:text-gray-400">
          Start a research query to generate your first report
        </p>
      </div>
    );
  }

  const report = currentReport || reports[0];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Report List */}
      <div className="lg:col-span-1">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Reports ({reports.length})
          </h2>
          <div className="space-y-2 max-h-[600px] overflow-y-auto">
            {reports.map((r) => (
              <motion.button
                key={r.id}
                whileHover={{ scale: 1.02 }}
                onClick={() => setCurrentReport(r)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  report.id === r.id
                    ? 'bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800'
                    : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {r.query}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {format(r.timestamp, 'MMM d, HH:mm')}
                </p>
              </motion.button>
            ))}
          </div>
        </div>
      </div>

      {/* Report Content */}
      <div className="lg:col-span-3">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  {report.report?.title || report.query}
                </h1>
                <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                  <span className="flex items-center">
                    <ClockIcon className="h-4 w-4 mr-1" />
                    {format(report.timestamp, 'MMM d, yyyy HH:mm')}
                  </span>
                  {report.processingTime && (
                    <span>{Math.round(report.processingTime)}ms</span>
                  )}
                  {report.evaluation && (
                    <span className="flex items-center">
                      <CheckCircleIcon className="h-4 w-4 mr-1 text-green-500" />
                      Score: {Math.round(report.evaluation.overall_score * 100)}%
                    </span>
                  )}
                </div>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => copyToClipboard(JSON.stringify(report.report, null, 2))}
                  className="p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                  aria-label="Copy report"
                >
                  <DocumentDuplicateIcon className="h-5 w-5" />
                </button>
                <button
                  onClick={() => downloadReport(report.report)}
                  className="p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                  aria-label="Download report"
                >
                  <ArrowDownTrayIcon className="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Report Sections */}
          <div className="p-6 space-y-4">
            {/* Executive Summary */}
            <ReportSection
              title="Executive Summary"
              isExpanded={expandedSections.includes('summary')}
              onToggle={() => toggleSection('summary')}
            >
              <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                {report.report?.executive_summary || 'No summary available'}
              </p>
            </ReportSection>

            {/* Key Findings */}
            {report.report?.key_findings && (
              <ReportSection
                title="Key Findings"
                isExpanded={expandedSections.includes('findings')}
                onToggle={() => toggleSection('findings')}
              >
                <ul className="space-y-2">
                  {report.report.key_findings.map((finding: string, index: number) => (
                    <li key={index} className="flex items-start">
                      <CheckCircleIcon className="h-5 w-5 text-green-500 mt-0.5 mr-2 flex-shrink-0" />
                      <span className="text-gray-700 dark:text-gray-300">{finding}</span>
                    </li>
                  ))}
                </ul>
              </ReportSection>
            )}

            {/* Recommendations */}
            {report.report?.recommendations && (
              <ReportSection
                title="Recommendations"
                isExpanded={expandedSections.includes('recommendations')}
                onToggle={() => toggleSection('recommendations')}
              >
                <ul className="space-y-2">
                  {report.report.recommendations.map((rec: string, index: number) => (
                    <li key={index} className="flex items-start">
                      <span className="text-primary-600 dark:text-primary-400 mr-2">
                        {index + 1}.
                      </span>
                      <span className="text-gray-700 dark:text-gray-300">{rec}</span>
                    </li>
                  ))}
                </ul>
              </ReportSection>
            )}

            {/* Evaluation */}
            {report.evaluation && (
              <ReportSection
                title="Performance Evaluation"
                isExpanded={expandedSections.includes('evaluation')}
                onToggle={() => toggleSection('evaluation')}
              >
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Overall Score</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {Math.round(report.evaluation.overall_score * 100)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Quality Assessment</p>
                    <p className="text-lg font-medium text-gray-900 dark:text-white">
                      {report.evaluation.quality_assessment || 'Good'}
                    </p>
                  </div>
                </div>
                {report.evaluation.improvement_areas && (
                  <div className="mt-4">
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Areas for Improvement:
                    </p>
                    <ul className="space-y-1">
                      {report.evaluation.improvement_areas.map((area: string, index: number) => (
                        <li key={index} className="flex items-start text-sm">
                          <ExclamationTriangleIcon className="h-4 w-4 text-yellow-500 mt-0.5 mr-2" />
                          <span className="text-gray-600 dark:text-gray-400">{area}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </ReportSection>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

interface ReportSectionProps {
  title: string;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

const ReportSection: React.FC<ReportSectionProps> = ({
  title,
  isExpanded,
  onToggle,
  children,
}) => {
  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors flex items-center justify-between"
      >
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
          {title}
        </h3>
        {isExpanded ? (
          <ChevronDownIcon className="h-5 w-5 text-gray-400" />
        ) : (
          <ChevronRightIcon className="h-5 w-5 text-gray-400" />
        )}
      </button>
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: 'auto' }}
            exit={{ height: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-4 bg-white dark:bg-gray-800">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ReportViewer;