import { useEffect, useState } from "react";
import { MdOutlineDarkMode, MdOutlineLightMode } from "react-icons/md";

export function ThemeToggle() {
  const [darkMode, setDarkMode] = useState(() => {
    if (typeof window === "undefined" || !window.matchMedia) {
      return false;
    }
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  return (
    <button
      aria-label="Toggle color mode"
      className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200"
      onClick={() => setDarkMode((prev) => !prev)}
    >
      {darkMode ? <MdOutlineLightMode /> : <MdOutlineDarkMode />}
      {darkMode ? "Light mode" : "Dark mode"}
    </button>
  );
}
