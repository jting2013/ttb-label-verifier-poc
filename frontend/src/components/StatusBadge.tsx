import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import type { ValidationStatus } from "../types/api";

const statusStyles: Record<ValidationStatus, string> = {
  PASS: "bg-green-50 text-green-800 ring-green-600/20",
  WARNING: "bg-yellow-50 text-yellow-900 ring-yellow-600/30",
  FAIL: "bg-red-50 text-red-800 ring-red-600/20"
};

export function StatusBadge({ status }: { status: ValidationStatus }) {
  const Icon = status === "PASS" ? CheckCircle2 : status === "WARNING" ? AlertTriangle : XCircle;
  return (
    <span className={`inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-semibold ring-1 ${statusStyles[status]}`}>
      <Icon aria-hidden="true" className="h-3.5 w-3.5" />
      {status}
    </span>
  );
}
