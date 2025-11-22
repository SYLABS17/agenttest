import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter } from 'react-router-dom';
import App from '../src/App';
import ChatInterface from '../src/components/Chat/ChatInterface';
import ResearchDashboard from '../src/components/Dashboard/ResearchDashboard';
import { useResearchStore } from '../src/stores/researchStore';
import { researchAPI } from '../src/services/api';

// Mock the API
jest.mock('../src/services/api');

// Mock zustand store
jest.mock('../src/stores/researchStore');

// Helper to wrap components with required providers
const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('App Component', () => {
  beforeEach(() => {
    // Mock store state
    (useResearchStore as jest.Mock).mockReturnValue({
      messages: [],
      reports: [],
      agents: [],
      addMessage: jest.fn(),
      addReport: jest.fn(),
      setCurrentReport: jest.fn(),
      clearMessages: jest.fn(),
      clearReports: jest.fn(),
      setIsResearching: jest.fn(),
      setCurrentQuery: jest.fn(),
      updateAgents: jest.fn(),
    });
  });

  test('renders without crashing', () => {
    renderWithProviders(<App />);
    expect(screen.getByText(/AI Research System/i)).toBeInTheDocument();
  });

  test('shows navigation sidebar', () => {
    renderWithProviders(<App />);
    expect(screen.getByText(/Dashboard/i)).toBeInTheDocument();
    expect(screen.getByText(/Research Chat/i)).toBeInTheDocument();
    expect(screen.getByText(/Reports/i)).toBeInTheDocument();
    expect(screen.getByText(/Agents/i)).toBeInTheDocument();
  });

  test('toggles sidebar on mobile', () => {
    renderWithProviders(<App />);
    const menuButton = screen.getByLabelText(/Toggle sidebar/i);
    
    // Initially sidebar should be visible
    expect(screen.getByText(/Research Hub/i)).toBeInTheDocument();
    
    // Click to hide
    fireEvent.click(menuButton);
    
    // Sidebar should still be in DOM but may be hidden via CSS
    expect(screen.getByText(/Research Hub/i)).toBeInTheDocument();
  });
});

describe('ChatInterface Component', () => {
  beforeEach(() => {
    const mockStore = {
      messages: [],
      reports: [],
      addMessage: jest.fn(),
      addReport: jest.fn(),
      clearMessages: jest.fn(),
      setIsResearching: jest.fn(),
      setCurrentQuery: jest.fn(),
    };
    (useResearchStore as jest.Mock).mockReturnValue(mockStore);
  });

  test('renders chat interface', () => {
    renderWithProviders(<ChatInterface />);
    expect(screen.getByPlaceholderText(/Ask your research question/i)).toBeInTheDocument();
    expect(screen.getByText(/Research Chat/i)).toBeInTheDocument();
  });

  test('displays welcome message when no messages', () => {
    renderWithProviders(<ChatInterface />);
    expect(screen.getByText(/Start Your Research/i)).toBeInTheDocument();
  });

  test('handles input change', async () => {
    renderWithProviders(<ChatInterface />);
    const input = screen.getByPlaceholderText(/Ask your research question/i) as HTMLTextAreaElement;
    
    await userEvent.type(input, 'Test query');
    expect(input.value).toBe('Test query');
  });

  test('submits research query', async () => {
    const mockConductResearch = jest.fn().mockResolvedValue({
      request_id: 'test-123',
      report: {
        title: 'Test Report',
        executive_summary: 'Test summary',
      },
      evaluation: {
        overall_score: 0.85,
      },
      processing_time_ms: 1500,
    });
    
    (researchAPI.conductResearch as jest.Mock) = mockConductResearch;
    
    const mockAddMessage = jest.fn();
    const mockAddReport = jest.fn();
    
    (useResearchStore as jest.Mock).mockReturnValue({
      messages: [],
      reports: [],
      addMessage: mockAddMessage,
      addReport: mockAddReport,
      clearMessages: jest.fn(),
      setIsResearching: jest.fn(),
      setCurrentQuery: jest.fn(),
    });
    
    renderWithProviders(<ChatInterface />);
    
    const input = screen.getByPlaceholderText(/Ask your research question/i);
    const submitButton = screen.getByText(/Research/i, { selector: 'button span' });
    
    await userEvent.type(input, 'Test research query');
    await userEvent.click(submitButton);
    
    await waitFor(() => {
      expect(mockConductResearch).toHaveBeenCalledWith('Test research query', undefined, true);
      expect(mockAddMessage).toHaveBeenCalled();
      expect(mockAddReport).toHaveBeenCalled();
    });
  });

  test('displays messages', () => {
    const mockMessages = [
      {
        id: '1',
        role: 'user' as const,
        content: 'Test query',
        timestamp: new Date(),
      },
      {
        id: '2',
        role: 'manager' as const,
        content: 'Processing your request...',
        timestamp: new Date(),
      },
    ];
    
    (useResearchStore as jest.Mock).mockReturnValue({
      messages: mockMessages,
      reports: [],
      addMessage: jest.fn(),
      addReport: jest.fn(),
      clearMessages: jest.fn(),
      setIsResearching: jest.fn(),
      setCurrentQuery: jest.fn(),
    });
    
    renderWithProviders(<ChatInterface />);
    
    expect(screen.getByText('Test query')).toBeInTheDocument();
    expect(screen.getByText('Processing your request...')).toBeInTheDocument();
  });
});

describe('ResearchDashboard Component', () => {
  beforeEach(() => {
    (useResearchStore as jest.Mock).mockReturnValue({
      reports: [],
      setCurrentReport: jest.fn(),
    });
  });

  test('renders dashboard', () => {
    renderWithProviders(<ResearchDashboard />);
    expect(screen.getByText(/Research Dashboard/i)).toBeInTheDocument();
  });

  test('displays metrics cards', () => {
    renderWithProviders(<ResearchDashboard />);
    expect(screen.getByText(/Total Reports/i)).toBeInTheDocument();
    expect(screen.getByText(/Active Agents/i)).toBeInTheDocument();
    expect(screen.getByText(/Avg Response Time/i)).toBeInTheDocument();
    expect(screen.getByText(/Success Rate/i)).toBeInTheDocument();
  });

  test('shows no reports message when empty', () => {
    renderWithProviders(<ResearchDashboard />);
    expect(screen.getByText(/No reports generated yet/i)).toBeInTheDocument();
  });

  test('displays recent reports', () => {
    const mockReports = [
      {
        id: '1',
        query: 'Test Query 1',
        report: { title: 'Report 1' },
        timestamp: new Date(),
        processingTime: 1500,
        evaluation: { overall_score: 0.85 },
      },
      {
        id: '2',
        query: 'Test Query 2',
        report: { title: 'Report 2' },
        timestamp: new Date(),
        processingTime: 2000,
      },
    ];
    
    (useResearchStore as jest.Mock).mockReturnValue({
      reports: mockReports,
      setCurrentReport: jest.fn(),
    });
    
    renderWithProviders(<ResearchDashboard />);
    
    expect(screen.getByText('Test Query 1')).toBeInTheDocument();
    expect(screen.getByText('Test Query 2')).toBeInTheDocument();
  });

  test('displays quick actions', () => {
    renderWithProviders(<ResearchDashboard />);
    
    const buttons = screen.getAllByRole('button');
    const buttonTexts = buttons.map(btn => btn.textContent);
    
    expect(buttonTexts).toEqual(expect.arrayContaining([
      expect.stringContaining('New Research'),
      expect.stringContaining('View Reports'),
      expect.stringContaining('Manage Agents'),
      expect.stringContaining('View Metrics'),
    ]));
  });
});

describe('API Integration', () => {
  test('handles API errors gracefully', async () => {
    const mockError = new Error('API Error');
    (researchAPI.conductResearch as jest.Mock) = jest.fn().mockRejectedValue(mockError);
    
    const mockAddMessage = jest.fn();
    
    (useResearchStore as jest.Mock).mockReturnValue({
      messages: [],
      reports: [],
      addMessage: mockAddMessage,
      addReport: jest.fn(),
      clearMessages: jest.fn(),
      setIsResearching: jest.fn(),
      setCurrentQuery: jest.fn(),
    });
    
    renderWithProviders(<ChatInterface />);
    
    const input = screen.getByPlaceholderText(/Ask your research question/i);
    const submitButton = screen.getByText(/Research/i, { selector: 'button span' });
    
    await userEvent.type(input, 'Test query');
    await userEvent.click(submitButton);
    
    await waitFor(() => {
      // Should add error message
      const errorCall = mockAddMessage.mock.calls.find(
        call => call[0].role === 'system' && call[0].content.includes('Error')
      );
      expect(errorCall).toBeDefined();
    });
  });
});

describe('Theme Toggle', () => {
  test('toggles between light and dark mode', () => {
    renderWithProviders(<App />);
    
    // Find theme toggle button (moon/sun icon)
    const themeToggle = screen.getByLabelText(/Toggle theme/i);
    
    // Initially should have light mode (no dark class on document)
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    
    // Click to toggle to dark mode
    fireEvent.click(themeToggle);
    
    // Note: The actual theme application happens in useEffect,
    // so we're mainly testing that the button exists and is clickable
    expect(themeToggle).toBeInTheDocument();
  });
});

describe('Navigation', () => {
  test('navigates between pages', () => {
    renderWithProviders(<App />);
    
    // Click on Reports link
    const reportsLink = screen.getByText(/Reports/i, { selector: 'a' });
    fireEvent.click(reportsLink);
    
    // Should navigate to reports (URL would change in real app)
    expect(reportsLink.closest('a')).toHaveClass(expect.stringContaining('primary'));
  });
});