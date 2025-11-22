type Props = {
  isDark: boolean;
  toggle: () => void;
};

export const DarkModeToggle = ({ isDark, toggle }: Props) => (
  <button
    type="button"
    onClick={toggle}
    className="inline-flex items-center rounded-full border border-slate-200 px-3 py-1 text-sm font-medium text-slate-700 shadow-sm transition hover:border-brand-500 hover:text-brand-600 dark:border-slate-700 dark:text-slate-200"
    aria-pressed={isDark}
  >
    {isDark ? "Light mode" : "Dark mode"}
  </button>
);
