import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../src/App';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

test('renders basic UI', () => {
  render(<App />);
  const linkElement = screen.getByText(/Azure AI Multi-Agent Research System/i);
  expect(linkElement).toBeInTheDocument();
});

test('submits search query', async () => {
  mockedAxios.post.mockResolvedValue({
    data: {
      report: {
        title: 'Research Report: Test',
        sections: [],
        metadata: { agents_involved: [] }
      },
      evaluation: {
        metrics: { latency_seconds: 0.5, accuracy_score: 0.9, relevance_score: 0.8 }
      }
    }
  });

  render(<App />);
  
  const input = screen.getByPlaceholderText(/Enter research topic.../i);
  fireEvent.change(input, { target: { value: 'Test Query' } });
  
  const button = screen.getByText(/Start Research/i);
  fireEvent.click(button);

  await waitFor(() => {
     expect(screen.getByText(/Research complete/i)).toBeInTheDocument();
  });
});
