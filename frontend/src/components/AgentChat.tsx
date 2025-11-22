import type { AgentMessage } from "../types";

type Props = {
  messages: AgentMessage[];
  loading: boolean;
};

const roleStyles: Record<string, string> = {
  system: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200",
  assistant: "bg-white text-slate-900 dark:bg-slate-700 dark:text-white"
};

export const AgentChat = ({ messages, loading }: Props) => (
  <section aria-label="Agent conversation" className="space-y-3">
    <header className="flex items-center justify-between">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Group Chat</h2>
      {loading && <span className="text-sm text-amber-500">Agents collaborating…</span>}
    </header>
    <div className="space-y-2 max-h-96 overflow-y-auto pr-2" role="log">
      {messages.map((message, index) => (
        <article
          key={`${message.agent}-${index}`}
          className={`rounded-xl border border-slate-200/70 p-4 shadow-sm dark:border-slate-600 ${
            roleStyles[message.role] ?? roleStyles.assistant
          }`}
        >
          <header className="flex items-center justify-between pb-2">
            <span className="font-medium">{message.agent}</span>
            {message.latency_ms !== undefined && (
              <span className="text-xs text-slate-500">{message.latency_ms} ms</span>
            )}
          </header>
          <p className="text-sm leading-relaxed">{message.content}</p>
          {message.citations && message.citations.length > 0 && (
            <ul className="mt-2 list-disc pl-5 text-xs text-slate-600 dark:text-slate-300">
              {message.citations.map((citation) => (
                <li key={citation}>{citation}</li>
              ))}
            </ul>
          )}
        </article>
      ))}
      {!messages.length && (
        <p className="text-sm text-slate-500">Submit a query to start the conversation.</p>
      )}
    </div>
  </section>
);
