import { useCallback, useEffect, useMemo, useState } from "react";
import { AgentMessage, FinalReport, ResearchResponse } from "./types";
import { QueryInput } from "./components/QueryInput";
import { ChatPanel } from "./components/ChatPanel";
import { ReportViewer } from "./components/ReportViewer";
import { ObservabilityPanel } from "./components/ObservabilityPanel";
import { LogsPanel } from "./components/LogsPanel";
import { ThemeToggle } from "./components/ThemeToggle";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const presetQueries = [
  "Future of renewable energy in Africa",
  "Impact of generative AI on journalism",
];

function App() {
  const [query, setQuery] = useState(presetQueries[0]);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [report, setReport] = useState<FinalReport | undefined>();
  const [latency, setLatency] = useState<Record<string, number>>({});
  const [evaluation, setEvaluation] = useState<ResearchResponse["evaluation"]>({});
  const [logs, setLogs] = useState<Record<string, unknown>[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/logs`);
      if (!res.ok) throw new Error("Unable to pull logs");
      const body = await res.json();
      setLogs(body.logs ?? []);
    } catch (err) {
      console.warn("log fetch failed", err);
    }
  }, [API_BASE_URL]);

  useEffect(() => {
    fetchLogs();
    const id = setInterval(fetchLogs, 15000);
    return () => clearInterval(id);
  }, [fetchLogs]);

  const runResearch = async () => {
    if (!query.trim()) {
      setError("Please provide a research prompt.");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/research`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      if (!response.ok) {
        throw new Error("Research request failed");
      }
      const data: ResearchResponse = await response.json();
      setMessages(data.conversation);
      setReport(data.final_report);
      setLatency(data.latency);
      setEvaluation(data.evaluation);
      await fetchLogs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  };

  const heroSubtitle = useMemo(
    () => `Multi-agent research powered by Bing + Azure AI Search · v${__APP_VERSION__}`,
    []
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-100 via-white to-slate-100 p-4 dark:from-slate-900 dark:via-slate-900 dark:to-slate-800">
      <main className="mx-auto flex max-w-6xl flex-col gap-6 py-6">
        <header className="flex flex-col gap-4 rounded-3xl bg-white/90 p-6 shadow-card dark:bg-slate-800/80 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-widest text-slate-400 dark:text-slate-500">Azure AI Foundry</p>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Research Orchestrator</h1>
            <p className="text-sm text-slate-500 dark:text-slate-300">{heroSubtitle}</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <select
              aria-label="Sample queries"
              className="rounded-full border border-slate-200 px-3 py-1 text-sm dark:border-slate-700 dark:bg-slate-900"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            >
              {presetQueries.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
            <ThemeToggle />
          </div>
        </header>

        <QueryInput value={query} onChange={setQuery} onSubmit={runResearch} disabled={isLoading} />
        {error && (
          <div role="alert" className="rounded-xl border border-rose-300 bg-rose-50 p-3 text-sm text-rose-700">
            {error}
          </div>
        )}

        <div className="grid gap-6 md:grid-cols-2">
          <ChatPanel messages={messages} />
          <ReportViewer report={report} />
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <div className="md:col-span-2">
            <ObservabilityPanel latencies={latency} evaluation={evaluation} />
          </div>
          <LogsPanel logs={logs} />
        </div>
      </main>
    </div>
  );
}

export default App;
