export type Status = "success" | "running" | "warning" | "failed" | "blocked" | "not_started";

export interface Stage {
  id: string;
  label: string;
  status: Status;
  completed_at?: string;
  duration_seconds?: number;
}

export interface PlatformStatus {
  platform_status: Status;
  run_id: string | null;
  last_successful_run: string | null;
  pipeline_duration_seconds: number;
  freshness_seconds: number | null;
  tests: { passed: number; total: number };
  failed_pipelines: number;
  datasets_impacted: number;
  stages: Stage[];
}

export interface DatasetRun {
  dataset: string;
  source_row_count: number;
  raw_row_count: number;
  minio_object: string;
  file_size_bytes: number;
  started_at: string;
  duration_seconds: number;
  status: Status;
  stages: Record<string, Status>;
  error_message?: string;
}
