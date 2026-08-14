"""Best-effort lifecycle telemetry for an Airflow pipeline run."""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone

import psycopg


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--pipeline", default="adventureworks_pipeline")
    parser.add_argument("--status", choices=["running", "success", "warning", "failed"], required=True)
    parser.add_argument("--started-at")
    parser.add_argument("--error-message")
    return parser.parse_args()


def connection_string() -> str:
    return (
        f"host={os.getenv('WAREHOUSE_DB_HOST', 'warehouse')} "
        f"port={os.getenv('WAREHOUSE_DB_PORT', '5432')} "
        f"dbname={os.getenv('WAREHOUSE_DB_NAME', 'analytics')} "
        f"user={os.getenv('WAREHOUSE_DB_USER', 'analytics_user')} "
        f"password={os.getenv('WAREHOUSE_DB_PASSWORD', 'analytics_dev')}"
    )


def record(args: argparse.Namespace) -> None:
    now = datetime.now(timezone.utc)
    started_at = datetime.fromisoformat(args.started_at) if args.started_at else now
    finished_at = None if args.status == "running" else now
    with psycopg.connect(connection_string()) as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS observability")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS observability.pipeline_runs (
                run_id text PRIMARY KEY,
                pipeline_name text NOT NULL,
                started_at timestamptz NOT NULL,
                finished_at timestamptz,
                status text NOT NULL,
                duration_seconds numeric,
                error_message text
            )
            """
        )
        conn.execute(
            """
            INSERT INTO observability.pipeline_runs (
                run_id, pipeline_name, started_at, finished_at,
                status, duration_seconds, error_message
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (run_id) DO UPDATE SET
                finished_at = EXCLUDED.finished_at,
                status = EXCLUDED.status,
                duration_seconds = EXCLUDED.duration_seconds,
                error_message = EXCLUDED.error_message
            """,
            (
                args.run_id, args.pipeline, started_at, finished_at, args.status,
                (finished_at - started_at).total_seconds() if finished_at else None,
                args.error_message,
            ),
        )
        if args.status == "success":
            try:
                with conn.transaction():
                    conn.execute(
                        """
                        UPDATE observability.dataset_freshness
                        SET analytics_updated_at = %s, status = 'success'
                        WHERE run_id = %s
                        """,
                        (now, args.run_id),
                    )
            except psycopg.errors.UndefinedTable:
                pass


def main() -> None:
    args = parse_args()
    try:
        record(args)
        print(f"pipeline telemetry: run={args.run_id} status={args.status}")
    except Exception as exc:  # Telemetry must not fail the data pipeline.
        print(f"observability instrumentation failure: {exc}")


if __name__ == "__main__":
    main()
