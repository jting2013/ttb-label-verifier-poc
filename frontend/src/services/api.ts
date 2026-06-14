import type { BatchResponse, LabelReviewResult } from "../types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export async function uploadLabels(files: File[], applicationId: string): Promise<BatchResponse> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  formData.append("application_id", applicationId);

  const response = await fetch(`${API_BASE_URL}/api/labels/upload`, {
    method: "POST",
    body: formData
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function runSampleBatch(applicationId: string): Promise<BatchResponse> {
  const formData = new FormData();
  formData.append("application_id", applicationId);
  const response = await fetch(`${API_BASE_URL}/api/samples/demo`, {
    method: "POST",
    body: formData
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export async function fetchResults(): Promise<LabelReviewResult[]> {
  const response = await fetch(`${API_BASE_URL}/api/results`);
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export function downloadResultsCsv(results: LabelReviewResult[]): void {
  const headers = ["result_id", "filename", "application_id", "status", "field", "expected", "extracted", "field_status", "confidence", "message"];
  const rows = results.flatMap((result) =>
    result.validations.map((validation) => [
      result.result_id,
      result.filename,
      result.application_id,
      result.status,
      validation.field,
      validation.expected ?? "",
      validation.extracted ?? "",
      validation.status,
      validation.confidence.toString(),
      validation.message
    ])
  );
  const csv = [headers, ...rows]
    .map((row) => row.map((value) => `"${value.replace(/"/g, "\"\"")}"`).join(","))
    .join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = "ttb-label-review-results.csv";
  link.click();
  URL.revokeObjectURL(url);
}
