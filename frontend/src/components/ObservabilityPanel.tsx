type LatencyMap = Record<string, number>;

type Evaluation = Record<
  string,
  {
    accuracy: number;
    agreement: number;
    latency_ms: number;
  }
>;

type Props = {
  latencies: LatencyMap;
  evaluation: Evaluation;
};

export function ObservabilityPanel({ latencies, evaluation }: Props) {
  const agents = Object.keys({ ...latencies, ...evaluation });
  return (
    <section className="rounded-2xl bg-white/80 p-4 shadow-card dark:bg-slate-800/80">
      <header className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Observability</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">Latency + evaluation snapshots</p>
        </div>
      </header>
      {agents.length === 0 ? (
        <p className="text-sm text-slate-500 dark:text-slate-400">Run research to populate metrics.</p>
      ) : (
        <div className="grid gap-3 md:grid-cols-3">
          {agents.map((agent) => (
            <article
              key={agent}
              className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-900"
            >
              <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-100">{agent}</h3>
              <dl className="mt-2 space-y-1 text-xs text-slate-500 dark:text-slate-400">
                <div className="flex justify-between">
                  <dt>Latency</dt>
                  <dd>
                    {typeof latencies[agent] === "number" ? `${latencies[agent].toFixed(1)} ms` : "—"}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt>Accuracy</dt>
                  <dd>
                    {evaluation[agent] ? `${Math.round(evaluation[agent].accuracy * 100)}%` : "—"}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt>Agreement</dt>
                  <dd>
                    {evaluation[agent] ? `${Math.round(evaluation[agent].agreement * 100)}%` : "—"}
                  </dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
