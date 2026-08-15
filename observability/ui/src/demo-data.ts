import type { DatasetRun, PlatformStatus } from "./types";

const latestRun = "scheduled__2026-08-15T09:00:00-03:00";
const previousRun = "scheduled__2026-08-14T09:00:00-03:00";
const stages = { source: "success", minio: "success", raw: "success", staging: "success", intermediate: "success", analytics: "success", powerbi: "unmonitored" } as const;

export const demoDatasets: DatasetRun[] = [
  ["salesorderheader", 31_465, 31_465, 4_823_091], ["salesorderdetail", 121_317, 121_317, 12_984_220],
  ["customer", 19_820, 19_820, 2_145_732], ["product", 504, 504, 86_441], ["address", 19_614, 19_614, 1_765_309],
].map(([dataset, sourceRows, rawRows, bytes], index) => ({
  dataset: String(dataset), source_row_count: Number(sourceRows), raw_row_count: Number(rawRows),
  minio_object: `adventureworks/${dataset}/load_date=2026-08-15/part-000.parquet`, file_size_bytes: Number(bytes),
  started_at: `2026-08-15T09:0${index}:00-03:00`, duration_seconds: 18 + index * 4, status: "success", stages: { ...stages },
}));

const qualityResults = [
  ["not_null_fct_sales_order_key", "not_null", "error", 0, "pass"], ["unique_fct_sales_order_key", "unique", "error", 0, "pass"],
  ["relationships_sales_customer", "relationships", "error", 0, "pass"], ["accepted_values_order_status", "accepted_values", "warn", 3, "warn"],
].map(([name, type, severity, failed, status], index) => ({ invocation_id: "demo-dbt-20260815", test_unique_id: `test.demo.${index + 1}`, test_name: name, test_type: type, severity, failed_records: failed, execution_seconds: 0.42 + index * 0.17, status, depends_on: name === "accepted_values_order_status" ? ["source.adventure_works.sales.salesorderheader"] : [], message: failed ? "3 pedidos históricos usam um status legado já mapeado." : "Teste concluído sem registros inválidos." }));

const demoDatasetTests = [
  ["salesorderheader", "not_null_salesorderheader_salesorderid", "not_null", "error", 0, "pass"],
  ["salesorderheader", "accepted_values_order_status", "accepted_values", "warn", 3, "warn"],
  ["salesorderdetail", "not_null_salesorderdetail_salesorderdetailid", "not_null", "error", 0, "pass"],
  ["salesorderdetail", "relationships_salesorderdetail_salesorderid", "relationships", "error", 0, "pass"],
  ["customer", "not_null_customer_customerid", "not_null", "error", 0, "pass"],
  ["customer", "unique_customer_customerid", "unique", "error", 0, "pass"],
  ["product", "not_null_product_productid", "not_null", "error", 0, "pass"],
  ["product", "unique_product_productid", "unique", "error", 0, "pass"],
  ["address", "not_null_address_addressid", "not_null", "error", 0, "pass"],
  ["address", "unique_address_addressid", "unique", "error", 0, "pass"],
].map(([dataset, name, type, severity, failed, status], index) => ({
  dataset, invocation_id: "demo-dbt-20260815", test_unique_id: `test.demo.dataset.${index + 1}`,
  test_name: name, test_type: type, severity, failed_records: failed,
  execution_seconds: 0.31 + index * 0.06, status,
  message: failed ? "3 pedidos históricos usam um status legado já mapeado." : "Teste concluído sem registros inválidos.",
}));

export const demo = {
  status: { platform_status: "success", run_id: latestRun, trigger_type: "scheduled", last_successful_run: "2026-08-15T09:08:42-03:00", pipeline_duration_seconds: 522, technical_freshness_seconds: 2_820, last_business_event_at: "2026-08-14T17:48:19-03:00", tests: { passed: 27, total: 28 }, failed_pipelines: 0, datasets_impacted: 0,
    stages: [["ingestion", "Ingestão", 174], ["freshness", "Freshness", 21], ["staging", "Staging", 66], ["intermediate", "Intermediate", 72], ["analytics", "Analytics", 103], ["tests", "Testes dbt", 48], ["powerbi", "Power BI", 0]].map(([id, label, seconds]) => ({ id: String(id), label: String(label), status: id === "powerbi" ? "unmonitored" : "success", completed_at: id === "powerbi" ? undefined : "2026-08-15T09:08:42-03:00", duration_seconds: Number(seconds) })),
  } as PlatformStatus,
  runs: [
    { run_id: latestRun, started_at: "2026-08-15T09:00:00-03:00", finished_at: "2026-08-15T09:08:42-03:00", duration_seconds: 522, status: "success", trigger_type: "scheduled" },
    { run_id: previousRun, started_at: "2026-08-14T09:00:00-03:00", finished_at: "2026-08-14T09:09:17-03:00", duration_seconds: 557, status: "success", trigger_type: "scheduled" },
    { run_id: "manual__2026-08-13T16:22:00-03:00", started_at: "2026-08-13T16:22:00-03:00", finished_at: "2026-08-13T16:31:41-03:00", duration_seconds: 581, status: "warning", trigger_type: "manual" },
    { run_id: "scheduled__2026-08-12T09:00:00-03:00", started_at: "2026-08-12T09:00:00-03:00", finished_at: "2026-08-12T09:08:06-03:00", duration_seconds: 486, status: "success", trigger_type: "scheduled" },
    { run_id: "scheduled__2026-08-11T09:00:00-03:00", started_at: "2026-08-11T09:00:00-03:00", finished_at: "2026-08-11T09:08:31-03:00", duration_seconds: 511, status: "success", trigger_type: "scheduled" },
    { run_id: "scheduled__2026-08-10T09:00:00-03:00", started_at: "2026-08-10T09:00:00-03:00", finished_at: "2026-08-10T09:10:04-03:00", duration_seconds: 604, status: "success", trigger_type: "scheduled" },
    { run_id: "scheduled__2026-08-09T09:00:00-03:00", started_at: "2026-08-09T09:00:00-03:00", finished_at: "2026-08-09T09:09:48-03:00", duration_seconds: 588, status: "success", trigger_type: "scheduled" },
    { run_id: "scheduled__2026-08-08T09:00:00-03:00", started_at: "2026-08-08T09:00:00-03:00", finished_at: "2026-08-08T09:07:59-03:00", duration_seconds: 479, status: "success", trigger_type: "scheduled" },
    { run_id: "scheduled__2026-08-07T09:00:00-03:00", started_at: "2026-08-07T09:00:00-03:00", finished_at: "2026-08-07T09:06:12-03:00", duration_seconds: 372, status: "failed", trigger_type: "scheduled" },
    { run_id: "scheduled__2026-08-06T09:00:00-03:00", started_at: "2026-08-06T09:00:00-03:00", finished_at: "2026-08-06T09:08:53-03:00", duration_seconds: 533, status: "success", trigger_type: "scheduled" },
  ],
  freshness: demoDatasets.map((row, index) => ({ dataset: row.dataset, source_updated_at: `2026-08-15T08:${42 - index}:00-03:00`, minio_updated_at: "2026-08-15T09:04:12-03:00", warehouse_updated_at: "2026-08-15T09:05:36-03:00", analytics_updated_at: "2026-08-15T09:07:54-03:00", status: "success" })),
  quality: { total: 28, passed: 27, warnings: 1, failed: 0, last_run_at: "2026-08-15T09:08:31-03:00", results: qualityResults },
  incidents: [{ occurred_at: "2026-08-13T16:31:41-03:00", origin: "dbt", severity: "warning", test_name: "accepted_values_order_status", error: "Status legado detectado e mantido para análise histórica.", invalid_records: 3 }],
};

export function demoRun(runId: string) {
  const run = demo.runs.find((item) => item.run_id === runId) || demo.runs[0];
  const failed = run.status === "failed";
  const warning = run.status === "warning";
  const warningTest = qualityResults.find((test) => test.status === "warn");
  return {
    ...run,
    datasets: demoDatasets,
    failure_scope: failed ? "orchestration" : warning ? "quality" : null,
    error_message: failed ? "A tarefa de consolidação do pipeline foi encerrada pelo Airflow após exceder o tempo limite." : null,
    failed_tests: warning && warningTest ? [{ ...warningTest, error_message: warningTest.message }] : [],
  };
}
export function demoDataset(name: string) { const row = demoDatasets.find((item) => item.dataset === name) || demoDatasets[0]; const tests = demoDatasetTests.filter((test) => test.dataset === row.dataset); return { dataset: row.dataset, ingestion: row, freshness: { freshness_type: row.dataset.startsWith("sales") ? "business" : "technical", age_seconds: 2820 }, stages: row.stages, tests }; }
export const demoEvidence = [{ sales_order_id: 75123, status: "Archived" }, { sales_order_id: 75187, status: "Archived" }, { sales_order_id: 75201, status: "Archived" }];
