from datetime import timedelta

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG


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
    tags=["adventureworks", "ingestion", "dbt"],
) as dag:

    ingest_raw = BashOperator(
        task_id="ingest_raw",
        bash_command=(
            "python "
            "/opt/airflow/project/python/ingestion/load_raw.py"
        ),
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            "DBT_LOG_PATH=/tmp/dbt-logs "
            "DBT_TARGET_PATH=/tmp/dbt-target "
            "dbt build "
            "--project-dir /opt/airflow/project/dbt/adventure_works "
            "--profiles-dir /opt/airflow/dbt"
        ),
    )

    ingest_raw >> dbt_build