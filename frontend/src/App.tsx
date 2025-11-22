import { useState, useEffect } from 'react'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { SunIcon, MoonIcon, BeakerIcon, ChartBarIcon, Cog6ToothIcon } from '@heroicons/react/24/outline'
import ResearchPage from './pages/ResearchPage'
import MetricsPage from './pages/MetricsPage'
import LogsPage from './pages/LogsPage'
import { ThemeProvider } from './utils/ThemeContext'
import { useTheme } from './utils/ThemeContext'

function AppContent() {
  const [isOnline, setIsOnline] = useState(true)
  const location = useLocation()
  const { theme, toggleTheme } = useTheme()

  useEffect(() => {
    // Check API health
    checkHealth()
    const interval = setInterval(checkHealth, 30000) // Check every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const checkHealth = async () => {
    try {
      const response = await fetch('/api/health')
      setIsOnline(response.ok)
    } catch {
      setIsOnline(false)
    }
  }

  const navItems = [
    { path: '/', label: 'Research', icon: BeakerIcon },
    { path: '/metrics', label: 'Metrics', icon: ChartBarIcon },
    { path: '/logs', label: 'Logs', icon: Cog6ToothIcon },
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo and Title */}
            <div className="flex items-center">
              <div className="flex-shrink-0 flex items-center">
                <BeakerIcon className="h-8 w-8 text-primary-600 dark:text-primary-400" />
                <span className="ml-2 text-xl font-semibold text-gray-900 dark:text-white">
                  AI Research System
                </span>
              </div>
              
              {/* Navigation */}
              <nav className="ml-10 flex space-x-4">
                {navItems.map((item) => {
                  const Icon = item.icon
                  const isActive = location.pathname === item.path
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`
                        inline-flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200
                        ${isActive
                          ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/50 dark:text-primary-300'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-white dark:hover:bg-gray-700'
                        }
                      `}
                      aria-current={isActive ? 'page' : undefined}
                    >
                      <Icon className="h-4 w-4 mr-1.5" aria-hidden="true" />
                      {item.label}
                    </Link>
                  )
                })}
              </nav>
            </div>

            {/* Right side controls */}
            <div className="flex items-center space-x-4">
              {/* Status Indicator */}
              <div className="flex items-center">
                <div
                  className={`
                    h-2 w-2 rounded-full mr-2 animate-pulse
                    ${isOnline ? 'bg-green-500' : 'bg-red-500'}
                  `}
                  aria-hidden="true"
                />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {isOnline ? 'Online' : 'Offline'}
                </span>
              </div>

              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-white dark:hover:bg-gray-700 transition-colors duration-200"
                aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
              >
                {theme === 'light' ? (
                  <MoonIcon className="h-5 w-5" />
                ) : (
                  <SunIcon className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<ResearchPage />} />
          <Route path="/metrics" element={<MetricsPage />} />
          <Route path="/logs" element={<LogsPage />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="mt-auto bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              © 2024 AI Research System. Powered by Azure AI.
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Environment: {import.meta.env.MODE}
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  )
}

export default App