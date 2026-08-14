from datetime import timedelta
import subprocess

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG


DBT_PROJECT_DIR = "/opt/airflow/project/dbt/adventure_works"
DBT_PROFILES_DIR = "/opt/airflow/dbt"
PIPELINE_TELEMETRY = "/opt/airflow/project/python/observability/pipeline_run.py"


def finish_pipeline(context: dict, status: str) -> None:
    dag_run = context.get("dag_run")
    if not dag_run:
        return
    command = [
        "python", PIPELINE_TELEMETRY,
        "--run-id", dag_run.run_id,
        "--status", status,
        "--started-at", dag_run.start_date.isoformat(),
    ]
    if status == "failed" and context.get("exception"):
        command.extend(["--error-message", str(context["exception"])[:4000]])
    subprocess.run(command, check=False)


def pipeline_succeeded(context: dict) -> None:
    finish_pipeline(context, "success")


def pipeline_failed(context: dict) -> None:
    finish_pipeline(context, "failed")


def dbt_build_task(task_id: str, layer: str, selection: str) -> BashOperator:
    return BashOperator(
        task_id=task_id,
        bash_command=(
            "DBT_LOG_PATH=/tmp/dbt-logs "
            f"DBT_TARGET_PATH=/tmp/dbt-target/{{{{ ts_nodash }}}}/{layer} "
            f"dbt build --select {selection} "
            "--indirect-selection buildable "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROFILES_DIR}"
        ),
    )


def capture_build_task(task_id: str, layer: str) -> BashOperator:
    return BashOperator(
        task_id=task_id,
        bash_command=(
            "python "
            "/opt/airflow/project/python/observability/load_dbt_artifacts.py "
            f"--target-path /tmp/dbt-target/{{{{ ts_nodash }}}}/{layer} "
            "--orchestrator-run-id '{{ run_id }}' "
            "--allow-missing"
        ),
        trigger_rule="all_done",
    )


with DAG(
    dag_id="adventureworks_pipeline",
    description="Executa a ingestão RAW e constrói os modelos dbt",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="America/Sao_Paulo"),
    catchup=False,
    default_args={
        "owner": "data-engineering",
        "retries": 2,
        "retry_delay": timedelta(minutes=1),
    },
    on_success_callback=pipeline_succeeded,
    on_failure_callback=pipeline_failed,
    tags=["adventureworks", "ingestion", "dbt"],
) as dag:

    record_pipeline_start = BashOperator(
        task_id="record_pipeline_start",
        bash_command=(
            "python " + PIPELINE_TELEMETRY + " "
            "--run-id '{{ run_id }}' --status running "
            "--started-at '{{ dag_run.start_date.isoformat() }}'"
        ),
    )

    ingest_raw = BashOperator(
        task_id="ingest_raw",
        bash_command=(
            "INGESTION_RUN_ID='{{ run_id }}' python "
            "/opt/airflow/project/python/ingestion/load_raw.py"
        ),
    )

    dbt_source_freshness = BashOperator(
        task_id="dbt_source_freshness",
        bash_command=(
            "DBT_LOG_PATH=/tmp/dbt-logs "
            "DBT_TARGET_PATH=/tmp/dbt-target/{{ ts_nodash }}/freshness "
            "dbt source freshness "
            "--project-dir /opt/airflow/project/dbt/adventure_works "
            "--profiles-dir /opt/airflow/dbt"
        ),
    )

    capture_source_freshness = BashOperator(
        task_id="capture_source_freshness",
        bash_command=(
            "python "
            "/opt/airflow/project/python/observability/"
            "load_source_freshness.py "
            "--target-path /tmp/dbt-target/{{ ts_nodash }}/freshness "
            "--orchestrator-run-id '{{ run_id }}' "
            "--allow-missing"
        ),
        trigger_rule="all_done",
    )

    build_staging = dbt_build_task(
        task_id="build_staging",
        layer="staging",
        selection="path:models/staging",
    )

    build_intermediate = dbt_build_task(
        task_id="build_intermediate",
        layer="intermediate",
        selection="path:models/intermediate",
    )

    build_analytics = dbt_build_task(
        task_id="build_analytics",
        layer="analytics",
        selection="path:models/analytics --exclude mart_sales_details",
    )

    build_marts = dbt_build_task(
        task_id="build_marts",
        layer="marts",
        selection="mart_sales_details",
    )

    capture_staging = capture_build_task(
        task_id="capture_staging",
        layer="staging",
    )

    capture_intermediate = capture_build_task(
        task_id="capture_intermediate",
        layer="intermediate",
    )

    capture_analytics = capture_build_task(
        task_id="capture_analytics",
        layer="analytics",
    )

    capture_marts = capture_build_task(
        task_id="capture_marts",
        layer="marts",
    )

    record_pipeline_start >> ingest_raw >> dbt_source_freshness
    dbt_source_freshness >> capture_source_freshness
    (
        dbt_source_freshness
        >> build_staging
        >> build_intermediate
        >> build_analytics
        >> build_marts
    )
    build_staging >> capture_staging
    build_intermediate >> capture_intermediate
    build_analytics >> capture_analytics
    build_marts >> capture_marts
