import { FormEvent, useState } from "react";

type Props = {
  onSubmit: (query: string) => Promise<void> | void;
  loading: boolean;
  presets: string[];
};

export const ChatInput = ({ onSubmit, loading, presets }: Props) => {
  const [query, setQuery] = useState("");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!query.trim() || loading) return;
    await onSubmit(query.trim());
    setQuery("");
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-800"
    >
      <label htmlFor="research-query" className="text-sm font-medium text-slate-700 dark:text-slate-200">
        Research query
      </label>
      <textarea
        id="research-query"
        aria-label="Research query input"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        className="h-24 w-full rounded-xl border border-slate-200 bg-transparent p-3 text-sm text-slate-900 shadow-inner focus:border-brand-500 focus:outline-none dark:border-slate-600 dark:text-white"
        placeholder="Ask the Manager Agent anything…"
      />
      <div className="flex flex-wrap gap-2">
        {presets.map((preset) => (
          <button
            key={preset}
            type="button"
            onClick={() => setQuery(preset)}
            className="rounded-full border border-slate-200 px-3 py-1 text-xs text-slate-600 transition hover:border-brand-500 hover:text-brand-600 dark:border-slate-600 dark:text-slate-300"
          >
            {preset}
          </button>
        ))}
      </div>
      <button
        type="submit"
        disabled={loading}
        className="w-full rounded-xl bg-brand-600 px-4 py-2 text-white shadow transition hover:bg-brand-500 disabled:cursor-not-allowed disabled:bg-slate-400"
      >
        {loading ? "Running agents…" : "Generate report"}
      </button>
    </form>
  );
};
