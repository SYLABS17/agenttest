import React, { useState } from 'react';

interface ChatInterfaceProps {
  onSubmit: (query: string) => void;
  loading: boolean;
  logs: string[];
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onSubmit, loading, logs }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSubmit(query);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto bg-white shadow-lg rounded-lg overflow-hidden">
      <div className="p-4 bg-gray-100 border-b">
        <h2 className="text-lg font-semibold text-gray-800">Research Assistant</h2>
      </div>
      <div className="p-4 h-64 overflow-y-auto bg-gray-50">
        {logs.length === 0 && <p className="text-gray-500 text-center mt-4">Start a research task...</p>}
        {logs.map((log, idx) => (
          <div key={idx} className="mb-2 text-sm text-gray-700 font-mono">
            {log}
          </div>
        ))}
        {loading && (
           <div className="flex items-center justify-center mt-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
           </div>
        )}
      </div>
      <div className="p-4 bg-white border-t">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter research topic..."
            className="flex-1 p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button
            type="submit"
            className={`px-4 py-2 rounded text-white ${loading ? 'bg-gray-400' : 'bg-blue-500 hover:bg-blue-600'}`}
            disabled={loading}
          >
            Start Research
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
