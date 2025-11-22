import { FinalReport } from "../types";

type Props = {
  report?: FinalReport;
};

export function ReportViewer({ report }: Props) {
  return (
    <section className="rounded-2xl bg-white/80 p-5 shadow-card dark:bg-slate-800/80" aria-live="polite">
      <header className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Final research report</h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">Aggregated by the manager agent</p>
        </div>
      </header>
      {!report ? (
        <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">Run a query to generate a report.</p>
      ) : (
        <article className="mt-4 space-y-4">
          <div>
            <p className="text-xs uppercase tracking-widest text-slate-400 dark:text-slate-500">Title</p>
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white">{report.title}</h3>
          </div>
          <div>
            <p className="text-xs uppercase tracking-widest text-slate-400 dark:text-slate-500">Summary</p>
            <p className="text-slate-700 dark:text-slate-200">{report.summary}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-widest text-slate-400 dark:text-slate-500">Key insights</p>
            <ul className="mt-2 list-disc space-y-2 pl-5 text-slate-700 dark:text-slate-200">
              {report.key_insights.map((insight) => (
                <li key={insight}>{insight}</li>
              ))}
            </ul>
          </div>
          {report.sources?.length > 0 && (
            <div>
              <p className="text-xs uppercase tracking-widest text-slate-400 dark:text-slate-500">Sources</p>
              <ul className="mt-2 space-y-1 text-sm">
                {report.sources.map((source) => (
                  <li key={source}>
                    <a className="text-sky-600 underline dark:text-sky-300" href={source} target="_blank" rel="noreferrer">
                      {source}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {report.next_steps?.length ? (
            <div>
              <p className="text-xs uppercase tracking-widest text-slate-400 dark:text-slate-500">Next steps</p>
              <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-200">
                {report.next_steps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
            </div>
          ) : null}
        </article>
      )}
    </section>
  );
}
