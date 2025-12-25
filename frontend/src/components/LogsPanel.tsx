type Props = {
  logs: Record<string, unknown>[];
};

export function LogsPanel({ logs }: Props) {
  return (
    <section className="rounded-2xl bg-white/80 p-4 shadow-card dark:bg-slate-800/80">
      <header className="mb-3 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Telemetry stream</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">Recent App Insights events</p>
        </div>
      </header>
      <div className="max-h-72 overflow-y-auto rounded-xl bg-slate-900/90 p-3 text-xs text-slate-100">
        {logs.length === 0 && <p className="text-slate-400">Telemetry will appear here after the first run.</p>}
        {logs.map((log, index) => (
          <pre key={index} className="mb-2 whitespace-pre-wrap break-words">
            {JSON.stringify(log, null, 2)}
          </pre>
        ))}
      </div>
    </section>
  );
}
