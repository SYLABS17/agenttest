import type { EvaluationScore, ObservabilityEntry } from "../types";

import { ScoreCard } from "./ScoreCard";

type Props = {
  evaluation: EvaluationScore | null;
  logs: ObservabilityEntry[];
};

export const ObservabilityPanel = ({ evaluation, logs }: Props) => (
  <section className="space-y-4" aria-label="Observability">
    <header>
      <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Observability</h2>
      <p className="text-sm text-slate-500">
        Latency, agent scores, and the most recent diagnostic events.
      </p>
    </header>
    {evaluation ? (
      <div className="grid gap-4 sm:grid-cols-2">
        <ScoreCard title="Overall" value={evaluation.overall} />
        <ScoreCard title="Agreement" value={evaluation.agreement} />
        <ScoreCard title="Accuracy" value={evaluation.accuracy} />
        <ScoreCard title="Latency Score" value={evaluation.latencyScore} />
      </div>
    ) : (
      <p className="text-sm text-slate-500">Run a query to populate metrics.</p>
    )}
    <div>
      <h3 className="text-sm font-semibold text-slate-700 dark:text-slate-200">Recent Logs</h3>
      <div className="mt-2 max-h-48 overflow-y-auto rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs dark:border-slate-700 dark:bg-slate-900">
        {logs.length ? (
          <ul className="space-y-1 font-mono">
            {logs.slice(-20).map((entry, index) => (
              <li key={`${entry.event}-${index}`}>
                <span className="text-brand-600">{entry.event}</span>:{" "}
                {JSON.stringify(entry)}
              </li>
            ))}
          </ul>
        ) : (
          <p>No logs yet.</p>
        )}
      </div>
    </div>
  </section>
);
