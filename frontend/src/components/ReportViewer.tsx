type Props = {
  report: string;
  query: string;
};

export const ReportViewer = ({ report, query }: Props) => (
  <section className="space-y-3" aria-live="polite">
    <header className="flex items-center justify-between">
      <div>
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Final Research Report</h2>
        <p className="text-sm text-slate-500">Query: {query || "—"}</p>
      </div>
    </header>
    <div className="rounded-xl border border-slate-200/70 bg-white p-4 text-sm leading-relaxed text-slate-800 shadow-sm dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100">
      {report ? (
        <article className="prose prose-slate max-w-none dark:prose-invert">
          {report.split("\n").map((line, index) => (
            <p key={`${line}-${index}`}>{line}</p>
          ))}
        </article>
      ) : (
        <p>No report generated yet.</p>
      )}
    </div>
  </section>
);
