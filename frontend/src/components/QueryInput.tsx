import { FormEvent } from "react";

type Props = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
};

export function QueryInput({ value, onChange, onSubmit, disabled }: Props) {
  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!disabled) {
      onSubmit();
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-3 rounded-2xl bg-white/80 p-4 shadow-card dark:bg-slate-800/80"
      aria-label="Research query form"
    >
      <label className="text-sm font-semibold text-slate-600 dark:text-slate-200" htmlFor="query">
        Research question
      </label>
      <textarea
        id="query"
        className="min-h-[100px] rounded-xl border border-slate-200 bg-slate-50 p-3 text-slate-900 outline-none focus:border-sky-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
        placeholder="e.g. Future of renewable energy in Africa"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-required
      />
      <button
        type="submit"
        className="inline-flex items-center justify-center rounded-xl bg-sky-600 px-4 py-2 font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:bg-sky-400"
        disabled={disabled}
        aria-busy={disabled}
      >
        {disabled ? "Researching…" : "Run research"}
      </button>
    </form>
  );
}
