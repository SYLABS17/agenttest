import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Message {
  id: string;
  role: 'user' | 'manager' | 'bing_search' | 'ai_search' | 'system';
  content: string;
  timestamp: Date;
  metadata?: any;
}

export interface ResearchReport {
  id: string;
  query: string;
  report: any;
  evaluation?: any;
  timestamp: Date;
  processingTime?: number;
}

export interface Agent {
  id: string;
  name: string;
  role: string;
  status: 'idle' | 'processing' | 'completed' | 'failed';
  metrics: any;
}

interface ResearchState {
  // Messages
  messages: Message[];
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  clearMessages: () => void;
  
  // Reports
  reports: ResearchReport[];
  currentReport: ResearchReport | null;
  addReport: (report: ResearchReport) => void;
  setCurrentReport: (report: ResearchReport | null) => void;
  clearReports: () => void;
  
  // Agents
  agents: Agent[];
  updateAgents: (agents: Agent[]) => void;
  
  // Research state
  isResearching: boolean;
  currentQuery: string;
  setIsResearching: (isResearching: boolean) => void;
  setCurrentQuery: (query: string) => void;
  
  // Error handling
  error: string | null;
  setError: (error: string | null) => void;
}

export const useResearchStore = create<ResearchState>()(
  persist(
    (set) => ({
      // Messages
      messages: [],
      addMessage: (message) =>
        set((state) => ({
          messages: [
            ...state.messages,
            {
              ...message,
              id: Math.random().toString(36).substr(2, 9),
              timestamp: new Date(),
            },
          ],
        })),
      clearMessages: () => set({ messages: [] }),
      
      // Reports
      reports: [],
      currentReport: null,
      addReport: (report) =>
        set((state) => ({
          reports: [report, ...state.reports].slice(0, 50), // Keep last 50 reports
          currentReport: report,
        })),
      setCurrentReport: (report) => set({ currentReport: report }),
      clearReports: () => set({ reports: [], currentReport: null }),
      
      // Agents
      agents: [],
      updateAgents: (agents) => set({ agents }),
      
      // Research state
      isResearching: false,
      currentQuery: '',
      setIsResearching: (isResearching) => set({ isResearching }),
      setCurrentQuery: (query) => set({ currentQuery: query }),
      
      // Error handling
      error: null,
      setError: (error) => set({ error }),
    }),
    {
      name: 'research-storage',
      partialize: (state) => ({
        reports: state.reports.slice(0, 10), // Only persist last 10 reports
        messages: state.messages.slice(-50), // Only persist last 50 messages
      }),
    }
  )
);