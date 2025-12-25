import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import App from '../src/App'
import ResearchPage from '../src/pages/ResearchPage'
import { apiService } from '../src/services/api'

// Mock the API service
vi.mock('../src/services/api', () => ({
  apiService: {
    getHealth: vi.fn(),
    conductResearch: vi.fn(),
    getMetrics: vi.fn(),
    getAgentsStatus: vi.fn(),
    getRecentLogs: vi.fn(),
    testDummyQuery: vi.fn(),
  },
}))

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )
    expect(screen.getByText('AI Research System')).toBeInTheDocument()
  })

  it('displays navigation links', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Research')).toBeInTheDocument()
    expect(screen.getByText('Metrics')).toBeInTheDocument()
    expect(screen.getByText('Logs')).toBeInTheDocument()
  })

  it('shows online/offline status', async () => {
    const mockHealth = { status: 'healthy' }
    ;(apiService.getHealth as any).mockResolvedValue(mockHealth)
    
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )
    
    await waitFor(() => {
      expect(screen.getByText('Online')).toBeInTheDocument()
    })
  })

  it('toggles dark mode', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    )
    
    const themeButton = screen.getByLabelText(/Switch to dark mode/i)
    fireEvent.click(themeButton)
    
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })
})

describe('ResearchPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders search form', () => {
    render(
      <BrowserRouter>
        <ResearchPage />
      </BrowserRouter>
    )
    
    expect(screen.getByLabelText(/Enter your research query/i)).toBeInTheDocument()
    expect(screen.getByText('Start Research')).toBeInTheDocument()
    expect(screen.getByText('Test with Dummy Query')).toBeInTheDocument()
  })

  it('displays sample queries', () => {
    render(
      <BrowserRouter>
        <ResearchPage />
      </BrowserRouter>
    )
    
    expect(screen.getByText('Future of renewable energy in Africa')).toBeInTheDocument()
    expect(screen.getByText('Impact of generative AI on journalism')).toBeInTheDocument()
  })

  it('handles form submission', async () => {
    const mockResponse = {
      success: true,
      query: 'test query',
      report: '# Test Report',
      chat_history: [],
      processing_time_ms: 1000,
    }
    ;(apiService.conductResearch as any).mockResolvedValue(mockResponse)
    
    render(
      <BrowserRouter>
        <ResearchPage />
      </BrowserRouter>
    )
    
    const input = screen.getByLabelText(/Enter your research query/i)
    const submitButton = screen.getByText('Start Research')
    
    fireEvent.change(input, { target: { value: 'test query' } })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(apiService.conductResearch).toHaveBeenCalledWith({
        query: 'test query',
        include_evaluation: true,
      })
    })
  })

  it('handles sample query selection', () => {
    render(
      <BrowserRouter>
        <ResearchPage />
      </BrowserRouter>
    )
    
    const sampleQuery = screen.getByText('Future of renewable energy in Africa')
    fireEvent.click(sampleQuery)
    
    const input = screen.getByLabelText(/Enter your research query/i) as HTMLInputElement
    expect(input.value).toBe('Future of renewable energy in Africa')
  })

  it('displays error messages', async () => {
    const errorMessage = 'API Error'
    ;(apiService.conductResearch as any).mockRejectedValue(new Error(errorMessage))
    
    render(
      <BrowserRouter>
        <ResearchPage />
      </BrowserRouter>
    )
    
    const input = screen.getByLabelText(/Enter your research query/i)
    const submitButton = screen.getByText('Start Research')
    
    fireEvent.change(input, { target: { value: 'test query' } })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('handles dummy query test', async () => {
    const mockResponse = {
      success: true,
      query: 'Future of renewable energy in Africa',
      report: '# Test Report',
      chat_history: [],
      processing_time_ms: 1000,
    }
    ;(apiService.testDummyQuery as any).mockResolvedValue(mockResponse)
    
    render(
      <BrowserRouter>
        <ResearchPage />
      </BrowserRouter>
    )
    
    const testButton = screen.getByText('Test with Dummy Query')
    fireEvent.click(testButton)
    
    await waitFor(() => {
      expect(apiService.testDummyQuery).toHaveBeenCalled()
    })
  })

  it('switches between tabs when results are shown', async () => {
    const mockResponse = {
      success: true,
      query: 'test query',
      report: '# Test Report',
      chat_history: [
        {
          id: '1',
          agent_name: 'ManagerAgent',
          content: 'Test message',
          metadata: {},
          timestamp: new Date().toISOString(),
        },
      ],
      evaluation: {
        query: 'test query',
        timestamp: new Date().toISOString(),
        agent_evaluations: [],
        agreement_score: 0.8,
        summary: {},
        recommendations: [],
      },
      processing_time_ms: 1000,
    }
    ;(apiService.conductResearch as any).mockResolvedValue(mockResponse)
    
    render(
      <BrowserRouter>
        <ResearchPage />
      </BrowserRouter>
    )
    
    const input = screen.getByLabelText(/Enter your research query/i)
    const submitButton = screen.getByText('Start Research')
    
    fireEvent.change(input, { target: { value: 'test query' } })
    fireEvent.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText('Agent Chat (1)')).toBeInTheDocument()
      expect(screen.getByText('Research Report')).toBeInTheDocument()
      expect(screen.getByText('Evaluation')).toBeInTheDocument()
    })
  })
})