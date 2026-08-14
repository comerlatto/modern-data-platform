from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

import psycopg
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row


app = FastAPI(
    title="Modern Data Platform Observability API",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("OBSERVABILITY_UI_ORIGIN", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


def connection_string() -> str:
    return (
        f"host={os.getenv('WAREHOUSE_DB_HOST', 'warehouse')} "
        f"port={os.getenv('WAREHOUSE_DB_PORT', '5432')} "
        f"dbname={os.getenv('WAREHOUSE_DB_NAME', 'analytics')} "
        f"user={os.getenv('WAREHOUSE_DB_USER', 'analytics_user')} "
        f"password={os.getenv('WAREHOUSE_DB_PASSWORD', 'analytics_dev')}"
    )


@contextmanager
def database() -> Iterator[psycopg.Connection[Any]]:
    try:
        with psycopg.connect(connection_string(), row_factory=dict_row) as conn:
            yield conn
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="Warehouse indisponível") from exc


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with database() as conn:
        try:
            return list(conn.execute(query, params).fetchall())
        except psycopg.errors.UndefinedTable:
            conn.rollback()
            return []


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    rows = fetch_all(query, params)
    return rows[0] if rows else None


def normalize_status(value: str | None) -> str:
    status = (value or "not_started").lower()
    if status in {"success", "pass", "passed"}:
        return "success"
    if status in {"warn", "warning"}:
        return "warning"
    if status in {"error", "fail", "failed", "runtime error"}:
        return "failed"
    if status in {"running", "started"}:
        return "running"
    if status == "blocked":
        return "blocked"
    return "not_started"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/platform/status")
def platform_status() -> dict[str, Any]:
    latest_pipeline = fetch_one(
        """
        select * from observability.pipeline_runs
        order by started_at desc limit 1
        """
    )
    target_run_id = latest_pipeline.get("run_id") if latest_pipeline else None
    latest_ingestion = fetch_one(
        """
        select run_id, max(finished_at) as finished_at,
               sum(duration_seconds) as duration_seconds,
               bool_and(status = 'success') as successful,
               bool_and(source_row_count is not null) as source_complete,
               bool_and(minio_uploaded_at is not null) as minio_complete,
               bool_and(raw_loaded_at is not null) as raw_complete,
               count(*) as datasets
        from observability.ingestion_runs
        where (%s::text is null or run_id = %s)
        group by run_id
        order by max(started_at) desc
        limit 1
        """,
        (target_run_id, target_run_id),
    )
    latest_dbt = fetch_one(
        """
        with latest as (
            select orchestrator_run_id from observability.dbt_runs
            where orchestrator_run_id is not null
            order by collected_at desc limit 1
        )
        select max(orchestrator_run_id) as orchestrator_run_id,
               max(collected_at) as collected_at,
               case
                 when count(*) = 0 then null
                 when bool_or(status in ('error', 'failed')) then 'error'
                 when bool_or(status in ('warn', 'warning')) then 'warn'
                 else 'success'
               end as status,
               sum(elapsed_seconds) as elapsed_seconds,
               sum(test_nodes) as test_nodes,
               sum(failed_tests) as failed_tests
        from observability.dbt_runs
        where orchestrator_run_id = coalesce(%s, (select orchestrator_run_id from latest))
        """,
        (target_run_id,),
    )
    freshness = fetch_one(
        """
        select max(snapshotted_at) as snapshotted_at,
               max(age_seconds) as max_age_seconds,
               count(*) filter (where status = 'pass') as healthy,
               count(*) as total
        from observability.source_freshness_results
        where invocation_id = (
            select invocation_id from observability.source_freshness_runs
            where (%s::text is null or orchestrator_run_id = %s)
            order by collected_at desc limit 1
        )
        """,
        (target_run_id, target_run_id),
    )

    dbt_status = normalize_status(latest_dbt.get("status") if latest_dbt else None)
    ingestion_status = (
        "success" if latest_ingestion and latest_ingestion.get("successful") else
        "failed" if latest_ingestion else "not_started"
    )
    pipeline_status = normalize_status(latest_pipeline.get("status") if latest_pipeline else None)
    overall = pipeline_status if pipeline_status != "not_started" else (
        "failed" if "failed" in {dbt_status, ingestion_status} else (
        "warning" if "warning" in {dbt_status, ingestion_status} else
        "success" if "success" in {dbt_status, ingestion_status} else "not_started"
    ))
    tests_total = int(latest_dbt.get("test_nodes") or 0) if latest_dbt else 0
    tests_failed = int(latest_dbt.get("failed_tests") or 0) if latest_dbt else 0
    run_id = (
        latest_pipeline.get("run_id") if latest_pipeline else None
    ) or (
        latest_dbt.get("orchestrator_run_id") if latest_dbt else None
    ) or (latest_ingestion.get("run_id") if latest_ingestion else None)
    source_status = ingestion_status if latest_ingestion and latest_ingestion.get("source_complete") else ("failed" if ingestion_status == "failed" else "not_started")
    minio_status = ingestion_status if latest_ingestion and latest_ingestion.get("minio_complete") else ("blocked" if source_status == "failed" else "not_started")
    raw_status = ingestion_status if latest_ingestion and latest_ingestion.get("raw_complete") else ("blocked" if minio_status in {"failed", "blocked"} else "not_started")
    dbt_visual = (
        "blocked"
        if raw_status in {"failed", "blocked", "not_started"}
        or (overall == "failed" and dbt_status == "not_started")
        else dbt_status
    )
    mart_status = "blocked" if dbt_visual in {"failed", "blocked"} else ("success" if dbt_visual == "success" else "not_started")

    return {
        "platform_status": overall,
        "run_id": run_id,
        "last_successful_run": (
            latest_pipeline.get("finished_at") if latest_pipeline and overall == "success" else
            latest_ingestion.get("finished_at") if latest_ingestion and overall == "success" else None
        ),
        "pipeline_duration_seconds": float(latest_pipeline.get("duration_seconds") or 0) if latest_pipeline else sum(filter(None, [
            float(latest_ingestion.get("duration_seconds") or 0) if latest_ingestion else 0,
            float(latest_dbt.get("elapsed_seconds") or 0) if latest_dbt else 0,
        ])),
        "freshness_seconds": float(freshness.get("max_age_seconds") or 0) if freshness else None,
        "tests": {"passed": tests_total - tests_failed, "total": tests_total},
        "failed_pipelines": 1 if overall == "failed" else 0,
        "datasets_impacted": tests_failed,
        "stages": [
            {"id": "source", "label": "Source", "status": source_status},
            {"id": "minio", "label": "MinIO", "status": minio_status},
            {"id": "raw", "label": "Raw", "status": raw_status},
            {"id": "dbt", "label": "dbt", "status": dbt_visual},
            {"id": "mart", "label": "Mart", "status": mart_status},
            {"id": "powerbi", "label": "Power BI", "status": "blocked" if mart_status in {"failed", "blocked"} else "not_started"},
        ],
    }


@app.get("/api/runs/latest")
def latest_run() -> dict[str, Any]:
    status = platform_status()
    return {
        "run_id": status["run_id"],
        "pipeline": "adventureworks_pipeline",
        "status": status["platform_status"],
        "stages": {stage["id"]: stage["status"] for stage in status["stages"]},
    }


@app.get("/api/pipelines")
def pipelines() -> list[dict[str, str]]:
    return [{"id": "adventureworks", "name": "AdventureWorks", "owner": "Data Engineering"}]


@app.get("/api/pipelines/{pipeline}/runs")
def pipeline_runs(pipeline: str, limit: int = Query(20, ge=1, le=100)) -> list[dict[str, Any]]:
    if pipeline != "adventureworks":
        raise HTTPException(status_code=404, detail="Pipeline não encontrado")
    return fetch_all(
        """
        select run_id, min(started_at) as started_at, max(finished_at) as finished_at,
               sum(duration_seconds) as duration_seconds,
               case when bool_and(status = 'success') then 'success' else 'failed' end as status,
               count(*) as dataset_count
        from observability.ingestion_runs
        group by run_id order by min(started_at) desc limit %s
        """,
        (limit,),
    )


@app.get("/api/runs/{run_id}")
def run_detail(run_id: str) -> dict[str, Any]:
    datasets = run_datasets(run_id)
    if not datasets:
        raise HTTPException(status_code=404, detail="Execução não encontrada")
    failed = [row for row in datasets if row["status"] == "failed"]
    return {
        "run_id": run_id,
        "status": "failed" if failed else "success",
        "datasets": datasets,
        "affected_datasets": [row["dataset"] for row in failed],
    }


@app.get("/api/runs/{run_id}/datasets")
def run_datasets(run_id: str) -> list[dict[str, Any]]:
    rows = fetch_all(
        """
        select source_table as dataset, source_row_count, raw_row_count,
               minio_object, file_size_bytes, started_at, minio_uploaded_at,
               raw_loaded_at, duration_seconds, status, error_message
        from observability.ingestion_runs
        where run_id = %s order by source_table
        """,
        (run_id,),
    )
    for row in rows:
        status = normalize_status(row.get("status"))
        row["status"] = status
        row["stages"] = {
            "source": status,
            "minio": status if row.get("minio_uploaded_at") else "not_started",
            "raw": status if row.get("raw_loaded_at") else "not_started",
            "dbt": "not_started",
            "mart": "not_started",
        }
    return rows


@app.get("/api/runs/{run_id}/tests")
def run_tests(run_id: str) -> list[dict[str, Any]]:
    return fetch_all(
        """
        select t.test_name, t.test_type, t.status, t.failures as failed_records,
               t.execution_seconds, t.message as error_message, t.depends_on,
               t.owner_name, t.owner_email
        from observability.dbt_test_results t
        join observability.dbt_runs r using (invocation_id)
        where r.orchestrator_run_id = %s
        order by t.status desc, t.test_name
        """,
        (run_id,),
    )


@app.get("/api/datasets/{dataset}")
def dataset_detail(dataset: str) -> dict[str, Any]:
    ingestion = fetch_one(
        """
        select * from observability.ingestion_runs
        where replace(source_table, '.', '_') = %s or source_table = %s
        order by started_at desc limit 1
        """,
        (dataset, dataset),
    )
    freshness = fetch_one(
        """
        select * from observability.source_freshness_results
        where table_name = %s order by snapshotted_at desc limit 1
        """,
        (dataset.split(".")[-1],),
    )
    tests = fetch_all(
        """
        select test_name, test_type, status, failures, message, execution_seconds
        from observability.dbt_test_results
        where depends_on::text ilike %s order by invocation_id desc
        limit 50
        """,
        (f"%{dataset.split('.')[-1]}%",),
    )
    if not ingestion and not freshness and not tests:
        raise HTTPException(status_code=404, detail="Dataset não encontrado")
    return {"dataset": dataset, "ingestion": ingestion, "freshness": freshness, "tests": tests}


@app.get("/api/datasets/{dataset}/history")
def dataset_history(dataset: str, limit: int = Query(50, ge=1, le=200)) -> list[dict[str, Any]]:
    return fetch_all(
        """
        select run_id, started_at, finished_at, source_row_count,
               raw_row_count, minio_object, file_size_bytes,
               duration_seconds, status, error_message
        from observability.ingestion_runs
        where replace(source_table, '.', '_') = %s or source_table = %s
        order by started_at desc limit %s
        """,
        (dataset, dataset, limit),
    )


@app.get("/api/freshness")
def freshness() -> list[dict[str, Any]]:
    return fetch_all(
        """
        select dataset_name as dataset, source_updated_at, minio_updated_at,
               warehouse_updated_at, analytics_updated_at, sla_minutes,
               case
                 when warehouse_updated_at is null then 'failed'
                 when analytics_updated_at is null then 'warning'
                 when extract(epoch from (current_timestamp - analytics_updated_at)) / 60 > sla_minutes then 'warning'
                 else status
               end as status
        from observability.dataset_freshness
        where run_id = (
            select run_id from observability.pipeline_runs
            order by started_at desc limit 1
        ) order by dataset_name
        """
    )


@app.get("/api/data-quality")
def data_quality() -> dict[str, Any]:
    results = fetch_all(
        """
        select test_name, test_type, status, failures as failed_records,
               execution_seconds, message, depends_on, owner_group, owner_name, owner_email
        from observability.dbt_test_results
        where invocation_id in (
            select invocation_id from observability.dbt_runs
            where orchestrator_run_id = (
                select orchestrator_run_id from observability.dbt_runs
                where orchestrator_run_id is not null
                order by collected_at desc limit 1
            )
        ) order by status desc, test_name
        """
    )
    return {
        "total": len(results),
        "passed": sum(normalize_status(row.get("status")) == "success" for row in results),
        "warnings": sum(normalize_status(row.get("status")) == "warning" for row in results),
        "failed": sum(normalize_status(row.get("status")) == "failed" for row in results),
        "results": results,
    }


@app.get("/api/incidents")
def incidents() -> list[dict[str, Any]]:
    return fetch_all(
        """
        select run_id, finished_at as occurred_at,
               'Ingestion: ' || source_table as test_name,
               status, null::bigint as invalid_records,
               error_message as error,
               to_jsonb(array[source_table]) as depends_on,
               null::text as owner_name, null::text as owner_email
        from observability.ingestion_runs
        where status = 'failed'
        union all
        select r.orchestrator_run_id as run_id, r.collected_at as occurred_at,
               t.test_name, t.status, t.failures as invalid_records,
               t.message as error, t.depends_on, t.owner_name, t.owner_email
        from observability.dbt_test_results t
        join observability.dbt_runs r using (invocation_id)
        where lower(t.status) in ('error', 'fail', 'failed', 'runtime error')
        order by occurred_at desc limit 100
        """
    )
