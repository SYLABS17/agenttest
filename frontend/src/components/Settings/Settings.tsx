import React, { useState } from 'react';
import { useQuery } from 'react-query';
import { systemAPI } from '../../services/api';
import {
  Cog6ToothIcon,
  BellIcon,
  ShieldCheckIcon,
  CloudIcon,
  DocumentTextIcon,
  PaintBrushIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';
import { useThemeStore } from '../../stores/themeStore';
import { useResearchStore } from '../../stores/researchStore';
import toast from 'react-hot-toast';
import { motion } from 'framer-motion';

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState('general');
  const { theme, toggleTheme } = useThemeStore();
  const { clearReports, clearMessages } = useResearchStore();
  
  const { data: config } = useQuery('config', systemAPI.getConfig);
  const { data: health } = useQuery('health', systemAPI.healthCheck);

  const tabs = [
    { id: 'general', label: 'General', icon: Cog6ToothIcon },
    { id: 'appearance', label: 'Appearance', icon: PaintBrushIcon },
    { id: 'notifications', label: 'Notifications', icon: BellIcon },
    { id: 'privacy', label: 'Privacy & Data', icon: ShieldCheckIcon },
    { id: 'azure', label: 'Azure Config', icon: CloudIcon },
    { id: 'about', label: 'About', icon: DocumentTextIcon },
  ];

  const handleClearData = () => {
    if (window.confirm('Are you sure you want to clear all local data? This action cannot be undone.')) {
      clearReports();
      clearMessages();
      localStorage.clear();
      toast.success('All local data cleared');
    }
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'general':
        return <GeneralSettings config={config} />;
      case 'appearance':
        return <AppearanceSettings theme={theme} toggleTheme={toggleTheme} />;
      case 'notifications':
        return <NotificationSettings />;
      case 'privacy':
        return <PrivacySettings onClearData={handleClearData} />;
      case 'azure':
        return <AzureSettings config={config} health={health} />;
      case 'about':
        return <AboutSettings config={config} health={health} />;
      default:
        return null;
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Settings
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Manage your application preferences and configuration
          </p>
        </div>

        <div className="flex">
          {/* Sidebar */}
          <div className="w-64 border-r border-gray-200 dark:border-gray-700">
            <nav className="p-4 space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center space-x-3 px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    activeTab === tab.id
                      ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <tab.icon className="h-5 w-5" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="flex-1 p-6">
            {renderTabContent()}
          </div>
        </div>
      </div>
    </div>
  );
};

// General Settings Component
const GeneralSettings: React.FC<{ config: any }> = ({ config }) => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          General Settings
        </h2>
      </div>

      <div className="space-y-4">
        <SettingItem
          label="Environment"
          value={config?.environment || 'development'}
          description="Current application environment"
        />
        <SettingItem
          label="Version"
          value={config?.version || '1.0.0'}
          description="Application version"
        />
        <SettingItem
          label="Debug Mode"
          value={config?.debug ? 'Enabled' : 'Disabled'}
          description="Debug mode status"
        />
        <SettingItem
          label="Agent Timeout"
          value={`${config?.agent_timeout || 30} seconds`}
          description="Maximum time for agent responses"
        />
        <SettingItem
          label="Max Retries"
          value={config?.max_retries || 3}
          description="Maximum retry attempts for failed operations"
        />
      </div>
    </div>
  );
};

// Appearance Settings Component
const AppearanceSettings: React.FC<{ theme: string; toggleTheme: () => void }> = ({
  theme,
  toggleTheme,
}) => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Appearance Settings
        </h2>
      </div>

      <div className="space-y-4">
        <div>
          <label className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                Dark Mode
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Toggle between light and dark themes
              </p>
            </div>
            <button
              onClick={toggleTheme}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                theme === 'dark' ? 'bg-primary-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  theme === 'dark' ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </label>
        </div>
      </div>

      <div className="pt-4">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          More appearance options coming soon...
        </p>
      </div>
    </div>
  );
};

// Notification Settings Component
const NotificationSettings: React.FC = () => {
  const [notifications, setNotifications] = useState({
    research_complete: true,
    errors: true,
    updates: false,
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Notification Settings
        </h2>
      </div>

      <div className="space-y-4">
        <ToggleSetting
          label="Research Complete"
          description="Notify when research queries are completed"
          checked={notifications.research_complete}
          onChange={(checked) =>
            setNotifications({ ...notifications, research_complete: checked })
          }
        />
        <ToggleSetting
          label="Error Alerts"
          description="Show notifications for errors and failures"
          checked={notifications.errors}
          onChange={(checked) =>
            setNotifications({ ...notifications, errors: checked })
          }
        />
        <ToggleSetting
          label="System Updates"
          description="Receive notifications about system updates"
          checked={notifications.updates}
          onChange={(checked) =>
            setNotifications({ ...notifications, updates: checked })
          }
        />
      </div>
    </div>
  );
};

// Privacy Settings Component
const PrivacySettings: React.FC<{ onClearData: () => void }> = ({ onClearData }) => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Privacy & Data Settings
        </h2>
      </div>

      <div className="space-y-4">
        <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
          <p className="text-sm text-yellow-800 dark:text-yellow-200">
            Your data is stored locally in your browser. No personal information is sent to external servers.
          </p>
        </div>

        <div className="space-y-2">
          <h3 className="text-sm font-medium text-gray-900 dark:text-white">
            Data Management
          </h3>
          <button
            onClick={onClearData}
            className="btn-outline text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20"
          >
            Clear All Local Data
          </button>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            This will delete all reports, messages, and settings from your browser
          </p>
        </div>
      </div>
    </div>
  );
};

// Azure Settings Component
const AzureSettings: React.FC<{ config: any; health: any }> = ({ config, health }) => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Azure Configuration
        </h2>
      </div>

      <div className="space-y-4">
        <StatusItem
          label="Azure Services"
          status={config?.azure_configured ? 'Configured' : 'Not Configured'}
          isHealthy={config?.azure_configured}
        />
        <StatusItem
          label="Observability"
          status={config?.observability_configured ? 'Configured' : 'Not Configured'}
          isHealthy={config?.observability_configured}
        />
        <StatusItem
          label="Manager Agent"
          status={health?.services?.manager_agent || 'unavailable'}
          isHealthy={health?.services?.manager_agent === 'healthy'}
        />
        <StatusItem
          label="Evaluation Service"
          status={health?.services?.evaluation_service || 'unavailable'}
          isHealthy={health?.services?.evaluation_service === 'healthy'}
        />
      </div>

      <div className="pt-4 text-sm text-gray-500 dark:text-gray-400">
        <p>Azure configuration is managed through environment variables on the server.</p>
      </div>
    </div>
  );
};

// About Settings Component
const AboutSettings: React.FC<{ config: any; health: any }> = ({ config, health }) => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          About AI Research System
        </h2>
      </div>

      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
            System Information
          </h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500 dark:text-gray-400">Version</dt>
              <dd className="text-gray-900 dark:text-white">{config?.version || '1.0.0'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500 dark:text-gray-400">Environment</dt>
              <dd className="text-gray-900 dark:text-white">{config?.environment || 'development'}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500 dark:text-gray-400">Status</dt>
              <dd className="text-gray-900 dark:text-white">{health?.status || 'unknown'}</dd>
            </div>
          </dl>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
            Description
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            AI Research System is a multi-agent research platform powered by Azure AI services.
            It orchestrates multiple AI agents to conduct comprehensive research, providing
            detailed reports with analysis, insights, and recommendations.
          </p>
        </div>

        <div>
          <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
            Features
          </h3>
          <ul className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
            <li className="flex items-center">
              <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
              Multi-agent orchestration
            </li>
            <li className="flex items-center">
              <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
              Web and knowledge base search
            </li>
            <li className="flex items-center">
              <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
              Comprehensive research reports
            </li>
            <li className="flex items-center">
              <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
              Performance evaluation
            </li>
            <li className="flex items-center">
              <CheckIcon className="h-4 w-4 text-green-500 mr-2" />
              Real-time observability
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

// Helper Components
const SettingItem: React.FC<{
  label: string;
  value: string | number;
  description?: string;
}> = ({ label, value, description }) => (
  <div className="flex justify-between items-start">
    <div>
      <p className="text-sm font-medium text-gray-900 dark:text-white">{label}</p>
      {description && (
        <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
      )}
    </div>
    <span className="text-sm text-gray-900 dark:text-white font-mono">{value}</span>
  </div>
);

const StatusItem: React.FC<{
  label: string;
  status: string;
  isHealthy: boolean;
}> = ({ label, status, isHealthy }) => (
  <div className="flex justify-between items-center">
    <span className="text-sm font-medium text-gray-900 dark:text-white">{label}</span>
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        isHealthy
          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
          : 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
      }`}
    >
      {status}
    </span>
  </div>
);

const ToggleSetting: React.FC<{
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}> = ({ label, description, checked, onChange }) => (
  <label className="flex items-center justify-between cursor-pointer">
    <div>
      <p className="text-sm font-medium text-gray-900 dark:text-white">{label}</p>
      <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
    </div>
    <button
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        checked ? 'bg-primary-600' : 'bg-gray-200'
      }`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          checked ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  </label>
);

export default Settings;