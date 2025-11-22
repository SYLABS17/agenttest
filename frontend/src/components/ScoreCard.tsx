type Props = {
  title: string;
  value: number;
};

export const ScoreCard = ({ title, value }: Props) => (
  <article className="rounded-xl border border-slate-200 bg-white p-4 text-center shadow-sm dark:border-slate-700 dark:bg-slate-800">
    <p className="text-sm text-slate-500">{title}</p>
    <p className="text-3xl font-semibold text-brand-600">{(value * 100).toFixed(1)}%</p>
  </article>
);
