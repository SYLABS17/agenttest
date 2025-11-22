import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import ReportViewer from './components/ReportViewer';
import axios from 'axios';

function App() {
  const [report, setReport] = useState<any>(null);
  const [evaluation, setEvaluation] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);

  const handleResearch = async (query: string) => {
    setLoading(true);
    setReport(null);
    setEvaluation(null);
    setLogs([`Starting research on: "${query}"`]);

    try {
      // In a real app, we might use a websocket or SSE for real-time logs
      setLogs(prev => [...prev, "Manager Agent: dispatching tasks to Bing and AI Search..."]);
      
      // Simulate some delay for better UX
      await new Promise(r => setTimeout(r, 1000));
      setLogs(prev => [...prev, "Bing Agent: Searching web..."]);
      setLogs(prev => [...prev, "AI Search Agent: Searching internal documents..."]);

      const response = await axios.post('/api/research', { query });
      
      setLogs(prev => [...prev, "Manager Agent: Aggregating results..."]);
      setReport(response.data.report);
      setEvaluation(response.data.evaluation);
      setLogs(prev => [...prev, "Research complete."]);
      
    } catch (error) {
      console.error(error);
      setLogs(prev => [...prev, "Error: Failed to complete research."]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8 px-4">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-gray-800">Azure AI Multi-Agent Research System</h1>
        <p className="text-gray-600 mt-2">Powered by Azure OpenAI, Cognitive Search, and Bing</p>
      </header>
      
      <ChatInterface onSubmit={handleResearch} loading={loading} logs={logs} />
      
      <ReportViewer report={report} evaluation={evaluation} />
      
    </div>
  );
}

export default App;
