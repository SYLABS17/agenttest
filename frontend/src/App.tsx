import { useEffect, useState } from "react";

import { AgentChat } from "./components/AgentChat";
import { ChatInput } from "./components/ChatInput";
import { DarkModeToggle } from "./components/DarkModeToggle";
import { ObservabilityPanel } from "./components/ObservabilityPanel";
import { ReportViewer } from "./components/ReportViewer";
import { fetchLogs, runResearchQuery } from "./services/api";
import type { AgentMessage, EvaluationScore, ObservabilityEntry } from "./types";
import { useTheme } from "./hooks/useTheme";

const PRESETS = [
  "Future of renewable energy in Africa",
  "Impact of generative AI on journalism",
  "How can coastal cities decarbonize logistics?"
];

const App = () => {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [finalReport, setFinalReport] = useState("");
  const [currentQuery, setCurrentQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [evaluation, setEvaluation] = useState<EvaluationScore | null>(null);
  const [logs, setLogs] = useState<ObservabilityEntry[]>([]);
  const { isDark, toggle } = useTheme();

  const handleQuery = async (query: string) => {
    setLoading(true);
    setCurrentQuery(query);
    try {
      const response = await runResearchQuery(query);
      setMessages(response.messages);
      setFinalReport(response.finalReport);
      setEvaluation(response.evaluation);
      setLogs(await fetchLogs());
    } catch (error) {
      setMessages([
        {
          agent: "ManagerAgent",
          content: "Unable to complete the research request. Please retry.",
          role: "system"
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs().then(setLogs).catch(() => setLogs([]));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-6 text-slate-900 dark:bg-slate-900 dark:text-white">
      <main className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-col gap-3 rounded-3xl bg-gradient-to-r from-brand-500 to-indigo-500 p-6 text-white shadow-lg sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-wide">Azure AI research system</p>
            <h1 className="text-2xl font-semibold">Manager Agent Collaboration Hub</h1>
            <p className="text-sm text-white/80">
              FastAPI backend + React frontend orchestrating Bing & Azure AI Search workers.
            </p>
          </div>
          <DarkModeToggle isDark={isDark} toggle={toggle} />
        </header>

        <section className="grid gap-6 lg:grid-cols-[2fr,1.2fr]">
          <div className="space-y-6">
            <ChatInput onSubmit={handleQuery} loading={loading} presets={PRESETS} />
            <AgentChat messages={messages} loading={loading} />
            <ReportViewer report={finalReport} query={currentQuery} />
          </div>
          <ObservabilityPanel evaluation={evaluation} logs={logs} />
        </section>
      </main>
    </div>
  );
};

export default App;
