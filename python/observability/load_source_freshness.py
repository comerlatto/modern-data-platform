"""Persist dbt source freshness results in PostgreSQL."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import psycopg
from psycopg.types.json import Jsonb


SCHEMA = "observability"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-path", required=True, type=Path)
    parser.add_argument("--orchestrator-run-id")
    parser.add_argument("--allow-missing", action="store_true")
    return parser.parse_args()


def connection_string() -> str:
    return (
        f"host={os.getenv('WAREHOUSE_DB_HOST', 'warehouse')} "
        f"port={os.getenv('WAREHOUSE_DB_PORT', '5432')} "
        f"dbname={os.getenv('WAREHOUSE_DB_NAME', 'analytics')} "
        f"user={os.getenv('WAREHOUSE_DB_USER', 'analytics_user')} "
        f"password={os.getenv('WAREHOUSE_DB_PASSWORD', 'analytics_dev')}"
    )


def create_tables(connection: psycopg.Connection[Any]) -> None:
    connection.execute(
        f"""
        create schema if not exists {SCHEMA};

        create table if not exists {SCHEMA}.source_freshness_runs (
            invocation_id text primary key,
            orchestrator_run_id text,
            generated_at timestamptz,
            collected_at timestamptz not null default current_timestamp,
            dbt_version text,
            status text not null,
            elapsed_seconds numeric,
            total_sources integer not null,
            warned_sources integer not null,
            errored_sources integer not null
        );

        create table if not exists {SCHEMA}.source_freshness_results (
            invocation_id text not null references
                {SCHEMA}.source_freshness_runs(invocation_id),
            source_unique_id text not null,
            source_name text,
            table_name text,
            freshness_type text not null default 'technical',
            status text not null,
            max_loaded_at timestamptz,
            snapshotted_at timestamptz,
            age_seconds numeric,
            criteria jsonb not null,
            execution_seconds numeric,
            error_message text,
            primary key (invocation_id, source_unique_id)
        );

        alter table {SCHEMA}.source_freshness_results
            add column if not exists freshness_type text not null default 'technical';

        create index if not exists idx_source_freshness_status
            on {SCHEMA}.source_freshness_results(status, snapshotted_at);
        """
    )


def overall_status(results: list[dict[str, Any]]) -> str:
    statuses = {
        str(result.get("status", "")).lower()
        for result in results
    }
    if statuses & {"error", "runtime error"}:
        return "error"
    if "warn" in statuses:
        return "warn"
    return "success"


def source_parts(unique_id: str) -> tuple[str | None, str | None]:
    parts = unique_id.split(".")
    if len(parts) < 4:
        return None, None
    return parts[-2], parts[-1]


def persist_freshness(
    connection: psycopg.Connection[Any],
    artifact: dict[str, Any],
    orchestrator_run_id: str | None,
    source_types: dict[str, str] | None = None,
) -> tuple[str, int]:
    metadata = artifact.get("metadata", {})
    results = artifact.get("results", [])
    invocation_id = metadata["invocation_id"]
    status = overall_status(results)
    warned_sources = sum(
        str(result.get("status", "")).lower() == "warn"
        for result in results
    )
    errored_sources = sum(
        str(result.get("status", "")).lower()
        in {"error", "runtime error"}
        for result in results
    )

    connection.execute(
        f"""
        insert into {SCHEMA}.source_freshness_runs (
            invocation_id,
            orchestrator_run_id,
            generated_at,
            dbt_version,
            status,
            elapsed_seconds,
            total_sources,
            warned_sources,
            errored_sources
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        on conflict (invocation_id) do update set
            orchestrator_run_id = excluded.orchestrator_run_id,
            generated_at = excluded.generated_at,
            collected_at = current_timestamp,
            dbt_version = excluded.dbt_version,
            status = excluded.status,
            elapsed_seconds = excluded.elapsed_seconds,
            total_sources = excluded.total_sources,
            warned_sources = excluded.warned_sources,
            errored_sources = excluded.errored_sources
        """,
        (
            invocation_id,
            orchestrator_run_id,
            metadata.get("generated_at"),
            metadata.get("dbt_version"),
            status,
            artifact.get("elapsed_time"),
            len(results),
            warned_sources,
            errored_sources,
        ),
    )

    for result in results:
        unique_id = result["unique_id"]
        source_name, table_name = source_parts(unique_id)
        connection.execute(
            f"""
            insert into {SCHEMA}.source_freshness_results (
                invocation_id,
                source_unique_id,
                source_name,
                table_name,
                freshness_type,
                status,
                max_loaded_at,
                snapshotted_at,
                age_seconds,
                criteria,
                execution_seconds,
                error_message
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            on conflict (invocation_id, source_unique_id) do update set
                source_name = excluded.source_name,
                table_name = excluded.table_name,
                freshness_type = excluded.freshness_type,
                status = excluded.status,
                max_loaded_at = excluded.max_loaded_at,
                snapshotted_at = excluded.snapshotted_at,
                age_seconds = excluded.age_seconds,
                criteria = excluded.criteria,
                execution_seconds = excluded.execution_seconds,
                error_message = excluded.error_message
            """,
            (
                invocation_id,
                unique_id,
                source_name,
                table_name,
                (source_types or {}).get(unique_id, "technical"),
                result.get("status", "unknown"),
                result.get("max_loaded_at"),
                result.get("snapshotted_at"),
                result.get("max_loaded_at_time_ago_in_s"),
                Jsonb(result.get("criteria", {})),
                result.get("execution_time"),
                result.get("error"),
            ),
        )

    return status, len(results)


def main() -> None:
    args = parse_args()
    artifact_path = args.target_path / "sources.json"

    if not artifact_path.exists():
        message = f"dbt freshness artifact not found: {artifact_path}"
        if args.allow_missing:
            print(message)
            return
        raise FileNotFoundError(message)

    with artifact_path.open(encoding="utf-8") as file:
        artifact = json.load(file)

    manifest_path = args.target_path / "manifest.json"
    source_types: dict[str, str] = {}
    if manifest_path.exists():
        with manifest_path.open(encoding="utf-8") as file:
            manifest = json.load(file)
        source_types = {
            unique_id: str(node.get("meta", {}).get("freshness_type", "technical"))
            for unique_id, node in manifest.get("sources", {}).items()
        }

    with psycopg.connect(connection_string()) as connection:
        create_tables(connection)
        status, result_count = persist_freshness(
            connection,
            artifact,
            args.orchestrator_run_id,
            source_types,
        )

    print(
        "source freshness observability captured: "
        f"status={status}, sources={result_count}"
    )


if __name__ == "__main__":
    main()
