export type Status = "success" | "running" | "warning" | "failed" | "blocked" | "not_started" | "not_applicable" | "unmonitored";

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
  trigger_type: "manual" | "scheduled" | "other" | null;
  last_successful_run: string | null;
  pipeline_duration_seconds: number;
  technical_freshness_seconds: number | null;
  last_business_event_at: string | null;
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
  status_reason?: "quality_warning" | "quality_failed";
  stages: Record<string, Status>;
  error_message?: string;
}
