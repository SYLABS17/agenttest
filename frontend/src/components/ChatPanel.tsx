import { AgentMessage } from "../types";
import { clsx } from "clsx";

type Props = {
  messages: AgentMessage[];
};

const agentColors: Record<string, string> = {
  manager: "bg-sky-100 text-sky-900 dark:bg-sky-900/40 dark:text-sky-200",
  "bing-search": "bg-emerald-100 text-emerald-900 dark:bg-emerald-900/30 dark:text-emerald-100",
  "azure-ai-search": "bg-indigo-100 text-indigo-900 dark:bg-indigo-900/30 dark:text-indigo-100",
};

export function ChatPanel({ messages }: Props) {
  return (
    <section
      className="flex flex-col gap-4 rounded-2xl bg-white/80 p-4 shadow-card dark:bg-slate-800/80"
      aria-live="polite"
    >
      <header>
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Agent conversation</h2>
        <p className="text-sm text-slate-500 dark:text-slate-400">Real-time collaboration between manager and workers</p>
      </header>
      <div className="flex max-h-[400px] flex-col gap-3 overflow-y-auto pr-2">
        {messages.length === 0 && (
          <p className="text-sm text-slate-500 dark:text-slate-400">Submit a query to start the conversation.</p>
        )}
        {messages.map((message, index) => (
          <article
            key={`${message.sender}-${index}`}
            className={clsx(
              "rounded-xl p-3",
              agentColors[message.sender] ?? "bg-slate-100 text-slate-900 dark:bg-slate-700 dark:text-white"
            )}
          >
            <div className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-500 dark:text-slate-300">
              <span>{message.sender.replace("-", " ")}</span>
              <time dateTime={message.timestamp}>{new Date(message.timestamp).toLocaleTimeString()}</time>
            </div>
            <p className="mt-2 text-sm leading-relaxed">{message.message}</p>
            {message.insights && (
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                {message.insights.map((insight) => (
                  <li key={insight}>{insight}</li>
                ))}
              </ul>
            )}
            {message.sources && (
              <div className="mt-2 text-xs">
                <span className="font-semibold">Sources:</span>{" "}
                {message.sources.map((source) => (
                  <a
                    key={source}
                    href={source}
                    className="text-slate-800 underline dark:text-slate-200"
                    target="_blank"
                    rel="noreferrer"
                  >
                    {source}
                  </a>
                ))}
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}
