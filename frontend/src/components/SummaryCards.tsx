import type { BatchResponse } from "../types/api";

export function SummaryCards({ batch }: { batch: BatchResponse | null }) {
  const summary = batch?.summary ?? { total: 0, pass: 0, warning: 0, fail: 0 };
  const cards = [
    ["Total", summary.total, "border-slate-300"],
    ["Pass", summary.pass, "border-green-500"],
    ["Warning", summary.warning, "border-yellow-500"],
    ["Fail", summary.fail, "border-red-500"]
  ];

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {cards.map(([label, value, border]) => (
        <div key={label} className={`border-l-4 ${border} bg-white px-4 py-3 shadow-sm ring-1 ring-federal-line`}>
          <div className="text-sm font-medium text-slate-600">{label}</div>
          <div className="mt-1 text-2xl font-semibold text-federal-ink">{value}</div>
        </div>
      ))}
    </div>
  );
}
