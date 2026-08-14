import type { DatasetRun, PlatformStatus } from "./types";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json() as Promise<T>;
}

export const api = {
  status: () => request<PlatformStatus>("/api/platform/status"),
  runs: () => request<Record<string, unknown>[]>("/api/pipelines/adventureworks/runs"),
  run: (runId: string) => request<Record<string, unknown>>(`/api/runs/${encodeURIComponent(runId)}`),
  runDatasets: (runId: string) => request<DatasetRun[]>(`/api/runs/${encodeURIComponent(runId)}/datasets`),
  dataset: (name: string) => request<Record<string, unknown>>(`/api/datasets/${encodeURIComponent(name)}`),
  freshness: () => request<Record<string, unknown>[]>("/api/freshness"),
  quality: () => request<Record<string, unknown>>("/api/data-quality"),
  qualityEvidence: (invocationId: string, testId: string) => request<Record<string, unknown>[]>(`/api/data-quality/${encodeURIComponent(invocationId)}/${encodeURIComponent(testId)}/evidence`),
  incidents: () => request<Record<string, unknown>[]>("/api/incidents"),
};
