import { Download } from "lucide-react";
import { downloadResultsCsv } from "../services/api";
import type { LabelReviewResult } from "../types/api";
import { StatusBadge } from "./StatusBadge";

interface ResultsTableProps {
  results: LabelReviewResult[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function ResultsTable({ results, selectedId, onSelect }: ResultsTableProps) {
  return (
    <section className="bg-white ring-1 ring-federal-line">
      <div className="flex items-center justify-between border-b border-federal-line px-4 py-3">
        <h2 className="text-base font-semibold text-federal-ink">Validation Results</h2>
        <button
          className="inline-flex items-center gap-2 rounded border border-federal-line px-3 py-2 text-sm font-semibold text-federal-blue hover:bg-federal-mist disabled:cursor-not-allowed disabled:text-slate-400"
          disabled={results.length === 0}
          onClick={() => downloadResultsCsv(results)}
          type="button"
        >
          <Download className="h-4 w-4" aria-hidden="true" />
          Export CSV
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-federal-line text-sm">
          <thead className="bg-federal-mist text-left text-xs font-semibold uppercase tracking-wide text-slate-600">
            <tr>
              <th className="px-4 py-3">File</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">OCR</th>
              <th className="px-4 py-3">Confidence</th>
              <th className="px-4 py-3">Processing</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {results.length === 0 ? (
              <tr>
                <td className="px-4 py-8 text-center text-slate-500" colSpan={5}>
                  Results will appear after a batch is processed.
                </td>
              </tr>
            ) : (
              results.map((result) => (
                <tr
                  key={result.result_id}
                  className={`cursor-pointer hover:bg-blue-50 ${selectedId === result.result_id ? "bg-blue-50" : ""}`}
                  onClick={() => onSelect(result.result_id)}
                >
                  <td className="max-w-xs truncate px-4 py-3 font-medium text-federal-ink">{result.filename}</td>
                  <td className="px-4 py-3"><StatusBadge status={result.status} /></td>
                  <td className="px-4 py-3 text-slate-600">{result.ocr.engine}</td>
                  <td className="px-4 py-3 text-slate-600">{Math.round(result.ocr.confidence * 100)}%</td>
                  <td className="px-4 py-3 text-slate-600">{result.ocr.processing_ms} ms</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
