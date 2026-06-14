import { useEffect, useMemo, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { fetchResults, uploadLabels } from "./services/api";
import type { BatchResponse, LabelReviewResult } from "./types/api";
import { ComparisonPanel } from "./components/ComparisonPanel";
import { ResultsTable } from "./components/ResultsTable";
import { SettingsPanel } from "./components/SettingsPanel";
import { SummaryCards } from "./components/SummaryCards";
import { UploadPanel } from "./components/UploadPanel";

export default function App() {
  const [applicationId, setApplicationId] = useState("APP-OLD-TOM-001");
  const [batch, setBatch] = useState<BatchResponse | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const results = batch?.results ?? [];
  const selectedResult: LabelReviewResult | null = useMemo(
    () => results.find((result) => result.result_id === selectedId) ?? results[0] ?? null,
    [results, selectedId]
  );

  useEffect(() => {
    let active = true;
    fetchResults()
      .then((storedResults) => {
        if (!active || storedResults.length === 0) return;
        setBatch({
          batch_id: "recent-results",
          results: storedResults,
          summary: summarize(storedResults)
        });
        setSelectedId(storedResults[0].result_id);
      })
      .catch(() => {
        // The console remains usable when historical results are unavailable.
      });
    return () => {
      active = false;
    };
  }, []);

  async function handleUpload(files: File[]) {
    setBusy(true);
    setError(null);
    try {
      const response = await uploadLabels(files, applicationId);
      setBatch(response);
      setSelectedId(response.results[0]?.result_id ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen bg-federal-mist text-federal-ink">
      <header className="border-b border-federal-line bg-federal-navy text-white">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-4 lg:px-6">
          <ShieldCheck className="h-7 w-7" aria-hidden="true" />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-100">U.S. Treasury TTB Prototype</p>
            <h1 className="text-xl font-semibold">AI-Powered Alcohol Label Verification</h1>
          </div>
        </div>
      </header>

      <main>
        <UploadPanel busy={busy} onUpload={handleUpload} />
        <div className="mx-auto grid max-w-7xl gap-4 px-4 py-5 lg:grid-cols-[1fr_18rem] lg:px-6">
          <div className="space-y-4">
            <div className="rounded border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-slate-700">
              Prototype demonstration only. Do not upload sensitive or non-public information. Images are removed after processing.
            </div>
            {error && (
              <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">
                {error}
              </div>
            )}
            {busy && (
              <div className="rounded border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-federal-blue" role="status">
                OCR and validation are running. Typical label batches complete in a few seconds.
              </div>
            )}
            <SummaryCards batch={batch} />
            <ResultsTable results={results} selectedId={selectedResult?.result_id ?? null} onSelect={setSelectedId} />
            <ComparisonPanel result={selectedResult} />
          </div>
          <SettingsPanel applicationId={applicationId} onApplicationIdChange={setApplicationId} />
        </div>
      </main>
    </div>
  );
}

function summarize(results: LabelReviewResult[]) {
  return {
    total: results.length,
    pass: results.filter((result) => result.status === "PASS").length,
    warning: results.filter((result) => result.status === "WARNING").length,
    fail: results.filter((result) => result.status === "FAIL").length
  };
}
