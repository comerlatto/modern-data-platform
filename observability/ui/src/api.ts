import type { DatasetRun, PlatformStatus } from "./types";
import { demo, demoDataset, demoDatasets, demoEvidence, demoRun } from "./demo-data";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
export const isDemo = import.meta.env.VITE_DEMO_MODE === "true" || (!import.meta.env.DEV && !import.meta.env.VITE_API_URL);
const mock = <T>(value: T) => new Promise<T>((resolve) => setTimeout(() => resolve(value), 180));

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API}${path}`);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json() as Promise<T>;
}

export const api = {
  status: () => isDemo ? mock(demo.status) : request<PlatformStatus>("/api/platform/status"),
  runs: () => isDemo ? mock(demo.runs) : request<Record<string, unknown>[]>("/api/pipelines/adventureworks/runs"),
  run: (runId: string) => isDemo ? mock(demoRun(runId)) : request<Record<string, unknown>>(`/api/runs/${encodeURIComponent(runId)}`),
  runDatasets: (runId: string) => isDemo ? mock(demoDatasets) : request<DatasetRun[]>(`/api/runs/${encodeURIComponent(runId)}/datasets`),
  dataset: (name: string) => isDemo ? mock(demoDataset(name)) : request<Record<string, unknown>>(`/api/datasets/${encodeURIComponent(name)}`),
  freshness: () => isDemo ? mock(demo.freshness) : request<Record<string, unknown>[]>("/api/freshness"),
  quality: () => isDemo ? mock(demo.quality) : request<Record<string, unknown>>("/api/data-quality"),
  qualityEvidence: (invocationId: string, testId: string) => isDemo ? mock(testId.endsWith("4") ? demoEvidence : []) : request<Record<string, unknown>[]>(`/api/data-quality/${encodeURIComponent(invocationId)}/${encodeURIComponent(testId)}/evidence`),
  incidents: () => isDemo ? mock(demo.incidents) : request<Record<string, unknown>[]>("/api/incidents"),
};
