"""Persist dbt execution metadata and stored test failures in PostgreSQL."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


SCHEMA = "observability"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-path", required=True, type=Path)
    parser.add_argument("--orchestrator-run-id")
    parser.add_argument("--allow-missing", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def connection_string() -> str:
    return (
        f"host={os.getenv('WAREHOUSE_DB_HOST', 'warehouse')} "
        f"port={os.getenv('WAREHOUSE_DB_PORT', '5432')} "
        f"dbname={os.getenv('WAREHOUSE_DB_NAME', 'analytics')} "
        f"user={os.getenv('WAREHOUSE_DB_USER', 'analytics_user')} "
        f"password={os.getenv('WAREHOUSE_DB_PASSWORD', 'analytics_dev')}"
    )


def create_observability_tables(connection: psycopg.Connection[Any]) -> None:
    ddl = f"""
        create schema if not exists {SCHEMA};

        create table if not exists {SCHEMA}.dbt_runs (
            invocation_id text primary key,
            orchestrator_run_id text,
            generated_at timestamptz,
            collected_at timestamptz not null default current_timestamp,
            dbt_version text,
            command text,
            status text not null,
            elapsed_seconds numeric,
            total_nodes integer not null,
            test_nodes integer not null,
            failed_tests integer not null
        );

        create table if not exists {SCHEMA}.dbt_test_results (
            invocation_id text not null references {SCHEMA}.dbt_runs(invocation_id),
            test_unique_id text not null,
            test_name text not null,
            test_type text not null,
            status text not null,
            failures integer,
            execution_seconds numeric,
            message text,
            failure_relation text,
            depends_on jsonb not null,
            primary key (invocation_id, test_unique_id)
        );

        create table if not exists {SCHEMA}.dbt_test_failure_details (
            failure_detail_id bigint generated always as identity primary key,
            invocation_id text not null,
            test_unique_id text not null,
            captured_at timestamptz not null default current_timestamp,
            failure_record jsonb not null,
            foreign key (invocation_id, test_unique_id)
                references {SCHEMA}.dbt_test_results(invocation_id, test_unique_id)
                on delete cascade
        );

        create index if not exists idx_dbt_test_results_status
            on {SCHEMA}.dbt_test_results(status);

        create index if not exists idx_dbt_failure_details_test
            on {SCHEMA}.dbt_test_failure_details(test_unique_id, captured_at);
    """
    connection.execute(ddl)


def execution_status(results: list[dict[str, Any]]) -> str:
    failure_statuses = {"error", "fail", "failed", "runtime error"}
    warning_statuses = {"warn", "warning"}
    statuses = {str(result.get("status", "")).lower() for result in results}

    if statuses & failure_statuses:
        status = "error"
    elif statuses & warning_statuses:
        status = "warn"
    else:
        status = "success"

    return status


def integer_or_none(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def persist_run(
    connection: psycopg.Connection[Any],
    run_results: dict[str, Any],
    test_results: list[dict[str, Any]],
    orchestrator_run_id: str | None,
) -> str:
    metadata = run_results.get("metadata", {})
    args = run_results.get("args", {})
    invocation_id = metadata["invocation_id"]
    status = execution_status(run_results.get("results", []))
    failed_tests = sum(
        1
        for result in test_results
        if str(result.get("status", "")).lower()
        in {"error", "fail", "failed", "runtime error", "warn", "warning"}
    )

    connection.execute(
        f"""
        insert into {SCHEMA}.dbt_runs (
            invocation_id,
            orchestrator_run_id,
            generated_at,
            dbt_version,
            command,
            status,
            elapsed_seconds,
            total_nodes,
            test_nodes,
            failed_tests
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        on conflict (invocation_id) do update set
            orchestrator_run_id = excluded.orchestrator_run_id,
            generated_at = excluded.generated_at,
            collected_at = current_timestamp,
            dbt_version = excluded.dbt_version,
            command = excluded.command,
            status = excluded.status,
            elapsed_seconds = excluded.elapsed_seconds,
            total_nodes = excluded.total_nodes,
            test_nodes = excluded.test_nodes,
            failed_tests = excluded.failed_tests
        """,
        (
            invocation_id,
            orchestrator_run_id,
            metadata.get("generated_at"),
            metadata.get("dbt_version"),
            args.get("which"),
            status,
            run_results.get("elapsed_time"),
            len(run_results.get("results", [])),
            len(test_results),
            failed_tests,
        ),
    )
    return invocation_id


def persist_test_results(
    connection: psycopg.Connection[Any],
    invocation_id: str,
    manifest: dict[str, Any],
    test_results: list[dict[str, Any]],
) -> None:
    nodes = manifest.get("nodes", {})

    for result in test_results:
        unique_id = result["unique_id"]
        node = nodes.get(unique_id, {})
        test_metadata = node.get("test_metadata")
        test_type = "generic" if test_metadata else "singular"
        depends_on = node.get("depends_on", {}).get("nodes", [])

        connection.execute(
            f"""
            insert into {SCHEMA}.dbt_test_results (
                invocation_id,
                test_unique_id,
                test_name,
                test_type,
                status,
                failures,
                execution_seconds,
                message,
                failure_relation,
                depends_on
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            on conflict (invocation_id, test_unique_id) do update set
                test_name = excluded.test_name,
                test_type = excluded.test_type,
                status = excluded.status,
                failures = excluded.failures,
                execution_seconds = excluded.execution_seconds,
                message = excluded.message,
                failure_relation = excluded.failure_relation,
                depends_on = excluded.depends_on
            """,
            (
                invocation_id,
                unique_id,
                node.get("name", unique_id),
                test_type,
                result.get("status", "unknown"),
                integer_or_none(result.get("failures")),
                result.get("execution_time"),
                result.get("message"),
                node.get("relation_name"),
                Jsonb(depends_on),
            ),
        )


def relation_exists(
    connection: psycopg.Connection[Any], schema_name: str, relation_name: str
) -> bool:
    return bool(
        connection.execute(
            """
            select exists (
                select 1
                from information_schema.tables
                where table_schema = %s
                  and table_name = %s
            )
            """,
            (schema_name, relation_name),
        ).fetchone()[0]
    )


def persist_failure_details(
    connection: psycopg.Connection[Any],
    invocation_id: str,
    manifest: dict[str, Any],
    test_results: list[dict[str, Any]],
) -> int:
    nodes = manifest.get("nodes", {})
    captured_rows = 0

    for result in test_results:
        unique_id = result["unique_id"]
        node = nodes.get(unique_id, {})
        config = node.get("config", {})

        if not config.get("store_failures"):
            continue

        schema_name = node.get("schema")
        relation_name = node.get("alias")
        if not schema_name or not relation_name:
            continue

        if not relation_exists(connection, schema_name, relation_name):
            continue

        connection.execute(
            f"""
            delete from {SCHEMA}.dbt_test_failure_details
            where invocation_id = %s and test_unique_id = %s
            """,
            (invocation_id, unique_id),
        )

        query = sql.SQL("select * from {}.{}").format(
            sql.Identifier(schema_name),
            sql.Identifier(relation_name),
        )
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        for row in rows:
            connection.execute(
                f"""
                insert into {SCHEMA}.dbt_test_failure_details (
                    invocation_id,
                    test_unique_id,
                    failure_record
                )
                values (%s, %s, %s)
                """,
                (
                    invocation_id,
                    unique_id,
                    Jsonb(row, dumps=lambda value: json.dumps(value, default=str)),
                ),
            )
            captured_rows += 1

    return captured_rows


def main() -> None:
    args = parse_args()
    run_results_path = args.target_path / "run_results.json"
    manifest_path = args.target_path / "manifest.json"

    missing = [
        str(path)
        for path in (run_results_path, manifest_path)
        if not path.exists()
    ]
    if missing:
        message = f"dbt artifacts not found: {', '.join(missing)}"
        if args.allow_missing:
            print(message)
            return
        raise FileNotFoundError(message)

    run_results = load_json(run_results_path)
    manifest = load_json(manifest_path)
    nodes = manifest.get("nodes", {})
    test_results = [
        result
        for result in run_results.get("results", [])
        if nodes.get(result.get("unique_id"), {}).get("resource_type") == "test"
    ]

    with psycopg.connect(connection_string()) as connection:
        create_observability_tables(connection)
        invocation_id = persist_run(
            connection,
            run_results,
            test_results,
            args.orchestrator_run_id,
        )
        persist_test_results(connection, invocation_id, manifest, test_results)
        captured_rows = persist_failure_details(
            connection,
            invocation_id,
            manifest,
            test_results,
        )

    print(
        "dbt observability captured: "
        f"invocation_id={invocation_id}, "
        f"tests={len(test_results)}, "
        f"failure_rows={captured_rows}"
    )


if __name__ == "__main__":
    main()
