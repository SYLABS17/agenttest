import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import ResearchDashboard from './components/Dashboard/ResearchDashboard';
import ChatInterface from './components/Chat/ChatInterface';
import ReportViewer from './components/Report/ReportViewer';
import ObservabilityPanel from './components/Observability/ObservabilityPanel';
import AgentStatus from './components/Agents/AgentStatus';
import Settings from './components/Settings/Settings';
import { useThemeStore } from './stores/themeStore';
import { useResearchStore } from './stores/researchStore';

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { theme } = useThemeStore();
  
  useEffect(() => {
    // Apply theme class to document
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  return (
    <Router>
      <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
        {/* Sidebar */}
        <AnimatePresence>
          {sidebarOpen && (
            <motion.div
              initial={{ x: -250 }}
              animate={{ x: 0 }}
              exit={{ x: -250 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="fixed inset-y-0 left-0 z-50 w-64 lg:relative lg:z-auto"
            >
              <Sidebar onClose={() => setSidebarOpen(false)} />
            </motion.div>
          )}
        </AnimatePresence>
        
        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
          
          <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-gray-900">
            <div className="container mx-auto px-4 py-6">
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<ResearchDashboard />} />
                <Route path="/chat" element={<ChatInterface />} />
                <Route path="/reports" element={<ReportViewer />} />
                <Route path="/agents" element={<AgentStatus />} />
                <Route path="/observability" element={<ObservabilityPanel />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </div>
          </main>
        </div>
        
        {/* Mobile sidebar overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </div>
    </Router>
  );
}

export default App;