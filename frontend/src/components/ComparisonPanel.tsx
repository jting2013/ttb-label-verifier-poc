import type { LabelReviewResult } from "../types/api";
import { StatusBadge } from "./StatusBadge";

const labels: Record<string, string> = {
  brand_name: "Brand Name",
  class_type: "Class / Type",
  alcohol_content: "Alcohol Content",
  net_contents: "Net Contents",
  bottler_producer_name: "Bottler / Producer",
  country_of_origin: "Country of Origin",
  government_warning: "Government Warning"
};

function WarningText({ value }: { value: string | null }) {
  if (!value) return <>Not detected</>;
  const prefix = "GOVERNMENT WARNING:";
  if (!value.startsWith(prefix)) return <>{value}</>;
  return (
    <>
      <strong className="font-bold">{prefix}</strong>
      {value.slice(prefix.length)}
    </>
  );
}

export function ComparisonPanel({ result }: { result: LabelReviewResult | null }) {
  return (
    <section className="bg-white ring-1 ring-federal-line">
      <div className="border-b border-federal-line px-4 py-3">
        <h2 className="text-base font-semibold text-federal-ink">Expected vs Extracted</h2>
      </div>
      {!result ? (
        <div className="px-4 py-8 text-sm text-slate-500">Select a result to review field-level validation.</div>
      ) : (
        <>
          {result.image_url && (
            <div className="px-4 py-4">
              <div className="overflow-hidden rounded border border-slate-200 bg-slate-50">
                <img
                  src={result.image_url}
                  alt={`Label preview for ${result.filename}`}
                  className="h-80 w-full object-contain"
                />
              </div>
              <p className="mt-2 text-xs text-slate-500">Preview of the uploaded label image being inspected.</p>
            </div>
          )}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-federal-line text-sm">
            <thead className="bg-federal-mist text-left text-xs font-semibold uppercase tracking-wide text-slate-600">
              <tr>
                <th className="px-4 py-3">Field</th>
                <th className="px-4 py-3">Expected</th>
                <th className="px-4 py-3">Extracted</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Confidence</th>
                <th className="px-4 py-3">Explanation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 align-top">
              {result.validations.map((item) => {
                const isWarning = item.field === "government_warning";
                const boldObservation = result.ocr.format_observations?.government_warning_prefix_bold ?? null;
                return (
                  <tr key={item.field}>
                    <td className="px-4 py-3 font-medium text-federal-ink">{labels[item.field] ?? item.field}</td>
                    <td className="max-w-sm px-4 py-3 text-slate-700">
                      {isWarning ? <WarningText value={item.expected} /> : item.expected ?? "Not provided"}
                    </td>
                    <td className="max-w-sm px-4 py-3 text-slate-700">
                      {isWarning ? (
                        <>
                          <WarningText value={item.extracted} />
                          <p className="mt-2 text-xs font-medium text-slate-500">
                            Bold heading: {boldObservation === true ? "Verified" : boldObservation === false ? "Not compliant" : "Visual review required"}
                          </p>
                        </>
                      ) : item.extracted ?? "Not detected"}
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={item.status} /></td>
                    <td className="px-4 py-3 text-slate-700">{Math.round(item.confidence * 100)}%</td>
                    <td className="max-w-md px-4 py-3 text-slate-600">{item.message}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </>
      )}
    </section>
  );
}
