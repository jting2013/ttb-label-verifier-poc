import { Settings } from "lucide-react";

export function SettingsPanel({ applicationId, onApplicationIdChange }: { applicationId: string; onApplicationIdChange: (value: string) => void }) {
  return (
    <aside className="bg-white p-4 ring-1 ring-federal-line">
      <div className="mb-3 flex items-center gap-2">
        <Settings className="h-4 w-4 text-federal-blue" aria-hidden="true" />
        <h2 className="text-base font-semibold text-federal-ink">Review Configuration</h2>
      </div>
      <label className="block text-sm font-medium text-slate-700" htmlFor="application-id">
        Expected Application
      </label>
      <select
        id="application-id"
        className="mt-1 w-full rounded border border-federal-line bg-white px-3 py-2 text-sm text-federal-ink focus:border-federal-blue focus:outline-none focus:ring-2 focus:ring-blue-100"
        value={applicationId}
        onChange={(event) => onApplicationIdChange(event.target.value)}
      >
        <option value="APP-OLD-TOM-001">APP-OLD-TOM-001 - Old Tom Bourbon</option>
      </select>
      <dl className="mt-4 space-y-3 text-sm">
        <div>
          <dt className="font-medium text-slate-700">Workflow</dt>
          <dd className="text-slate-600">Upload, OCR, parse fields, validate, export.</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-700">OCR Mode</dt>
          <dd className="text-slate-600">Configured by backend environment variable.</dd>
        </div>
      </dl>
    </aside>
  );
}
