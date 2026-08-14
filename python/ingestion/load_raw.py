import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

import pyarrow as pa
import pyarrow.parquet as pq
import psycopg
from dotenv import load_dotenv
from minio import Minio
from minio.commonconfig import ENABLED
from minio.versioningconfig import VersioningConfig
from psycopg import sql


load_dotenv()


SOURCE_TABLES = [
    ("sales", "salesorderheader"),
    ("sales", "salesorderdetail"),
    ("sales", "customer"),
    ("sales", "salesterritory"),
    ("sales", "store"),
    ("sales", "specialoffer"),
    ("sales", "salesperson"),
    ("production", "product"),
    ("person", "person"),
    ("humanresources", "employee"),
]

SPOOL_MAX_SIZE = 64 * 1024 * 1024
LOAD_BATCH_SIZE = 5_000

OBJECT_TABLE_NAMES = {
    "salesorderheader": "sales_order_header",
    "salesorderdetail": "sales_order_detail",
    "salesterritory": "sales_territory",
    "specialoffer": "special_offer",
    "salesperson": "sales_person",
}


def create_connection(prefix: str) -> psycopg.Connection:
    return psycopg.connect(
        host=os.getenv(f"{prefix}_DB_HOST", "localhost"),
        dbname=os.environ[f"{prefix}_DB_NAME"],
        user=os.environ[f"{prefix}_DB_USER"],
        password=os.environ[f"{prefix}_DB_PASSWORD"],
        port=os.environ[f"{prefix}_DB_PORT"],
    )


def create_minio_client() -> Minio:
    secure = os.getenv("MINIO_SECURE", "false").lower() in {
        "1",
        "true",
        "yes",
    }

    return Minio(
        endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.getenv(
            "MINIO_ACCESS_KEY",
            os.getenv("MINIO_ROOT_USER", "minioadmin"),
        ),
        secret_key=os.getenv(
            "MINIO_SECRET_KEY",
            os.getenv("MINIO_ROOT_PASSWORD", "minioadmin123"),
        ),
        secure=secure,
    )


def ensure_versioned_bucket(client: Minio, bucket_name: str) -> None:
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)

    client.set_bucket_versioning(
        bucket_name,
        VersioningConfig(ENABLED),
    )


def get_ingestion_run_id() -> str:
    value = os.getenv("INGESTION_RUN_ID")
    if not value:
        value = datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%S%fZ"
        )

    return re.sub(r"[^A-Za-z0-9._-]", "_", value)


def build_object_name(
    loaded_at: datetime,
    table_name: str,
) -> str:
    object_table_name = OBJECT_TABLE_NAMES.get(table_name, table_name)
    load_date = loaded_at.date().isoformat()
    return (
        f"raw/{object_table_name}/load_date={load_date}/"
        f"{object_table_name}.parquet"
    )


def get_columns(
    source_conn: psycopg.Connection,
    schema_name: str,
    table_name: str,
) -> list[tuple[str, str]]:
    query = """
        SELECT
        attribute.attname,
        CASE
            WHEN column_type.typtype = 'd'
            THEN pg_catalog.format_type(
                column_type.typbasetype,
                column_type.typtypmod
            )
            ELSE pg_catalog.format_type(
                attribute.atttypid,
                attribute.atttypmod
            )
        END AS data_type
    FROM pg_catalog.pg_attribute AS attribute
    JOIN pg_catalog.pg_class AS table_metadata
        ON table_metadata.oid = attribute.attrelid
    JOIN pg_catalog.pg_namespace AS schema_metadata
        ON schema_metadata.oid = table_metadata.relnamespace
    JOIN pg_catalog.pg_type AS column_type
        ON column_type.oid = attribute.atttypid
    WHERE schema_metadata.nspname = %s
      AND table_metadata.relname = %s
      AND attribute.attnum > 0
      AND NOT attribute.attisdropped
    ORDER BY attribute.attnum
    """

    with source_conn.cursor() as cursor:
        cursor.execute(query, (schema_name, table_name))
        return cursor.fetchall()


def recreate_raw_table(
    warehouse_conn: psycopg.Connection,
    table_name: str,
    columns: list[tuple[str, str]],
) -> None:
    column_definitions = [
        sql.SQL("{} {}").format(
            sql.Identifier(column_name),
            sql.SQL(data_type),
        )
        for column_name, data_type in columns
    ]

    column_definitions.extend(
        [
            sql.SQL("_loaded_at timestamptz NOT NULL"),
            sql.SQL("_source_table text NOT NULL"),
        ]
    )

    drop_query = sql.SQL(
        "DROP TABLE IF EXISTS raw.{} CASCADE"
    ).format(
        sql.Identifier(table_name)
    )

    create_query = sql.SQL("CREATE TABLE raw.{} ({})").format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(column_definitions),
    )

    with warehouse_conn.cursor() as cursor:
        cursor.execute(drop_query)
        cursor.execute(create_query)


def normalize_for_arrow(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, memoryview):
        return bytes(value)
    return value


def export_table_to_parquet(
    source_conn: psycopg.Connection,
    schema_name: str,
    table_name: str,
    columns: list[tuple[str, str]],
    loaded_at: datetime,
    destination: tempfile.SpooledTemporaryFile,
) -> int:
    column_names = [column_name for column_name, _ in columns]
    source_table = f"{schema_name}.{table_name}"
    select_query = sql.SQL("SELECT {} FROM {}.{}").format(
        sql.SQL(", ").join(map(sql.Identifier, column_names)),
        sql.Identifier(schema_name),
        sql.Identifier(table_name),
    )

    with source_conn.cursor() as cursor:
        cursor.execute(select_query)
        rows = cursor.fetchall()

    parquet_data = {
        column_name: [
            normalize_for_arrow(row[index]) for row in rows
        ]
        for index, column_name in enumerate(column_names)
    }
    parquet_data["_loaded_at"] = [loaded_at] * len(rows)
    parquet_data["_source_table"] = [source_table] * len(rows)

    table = pa.table(parquet_data)
    pq.write_table(table, destination, compression="snappy")

    destination.seek(0)
    return len(rows)


def upload_snapshot(
    client: Minio,
    bucket_name: str,
    object_name: str,
    run_id: str,
    source_table: str,
    row_count: int,
    loaded_at: datetime,
    snapshot: tempfile.SpooledTemporaryFile,
) -> Optional[str]:
    snapshot.seek(0, os.SEEK_END)
    snapshot_size = snapshot.tell()
    snapshot.seek(0)

    result = client.put_object(
        bucket_name=bucket_name,
        object_name=object_name,
        data=snapshot,
        length=snapshot_size,
        content_type="application/vnd.apache.parquet",
        metadata={
            "source-table": source_table,
            "row-count": str(row_count),
            "loaded-at": loaded_at.isoformat(),
            "run-id": run_id,
        },
    )
    snapshot.seek(0)
    return result.version_id


def load_parquet_to_raw(
    warehouse_conn: psycopg.Connection,
    table_name: str,
    columns: list[tuple[str, str]],
    snapshot: tempfile.SpooledTemporaryFile,
) -> None:
    column_names = [column_name for column_name, _ in columns]
    column_names.extend(["_loaded_at", "_source_table"])
    copy_query = sql.SQL(
        "COPY raw.{} ({}) FROM STDIN"
    ).format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(map(sql.Identifier, column_names)),
    )

    snapshot.seek(0)
    parquet_file = pq.ParquetFile(snapshot)
    with warehouse_conn.cursor() as cursor:
        with cursor.copy(copy_query) as copy:
            for batch in parquet_file.iter_batches(
                batch_size=LOAD_BATCH_SIZE
            ):
                for record in batch.to_pylist():
                    copy.write_row(
                        tuple(record[name] for name in column_names)
                    )
    snapshot.seek(0)


def load_table(
    source_conn: psycopg.Connection,
    warehouse_conn: psycopg.Connection,
    minio_client: Minio,
    bucket_name: str,
    run_id: str,
    schema_name: str,
    table_name: str,
) -> int:
    source_table = f"{schema_name}.{table_name}"
    loaded_at = datetime.now(timezone.utc)
    columns = get_columns(source_conn, schema_name, table_name)
    object_name = build_object_name(
        loaded_at,
        table_name,
    )

    with tempfile.SpooledTemporaryFile(
        max_size=SPOOL_MAX_SIZE,
        mode="w+b",
    ) as snapshot:
        row_count = export_table_to_parquet(
            source_conn,
            schema_name,
            table_name,
            columns,
            loaded_at,
            snapshot,
        )
        version_id = upload_snapshot(
            minio_client,
            bucket_name,
            object_name,
            run_id,
            source_table,
            row_count,
            loaded_at,
            snapshot,
        )

        recreate_raw_table(warehouse_conn, table_name, columns)
        load_parquet_to_raw(
            warehouse_conn,
            table_name,
            columns,
            snapshot,
        )

    version_suffix = f" (versão {version_id})" if version_id else ""
    print(f"  MinIO: {bucket_name}/{object_name}{version_suffix}")
    print(f"  PostgreSQL: {row_count:,} registros copiados")

    return row_count


def main() -> None:
    bucket_name = os.getenv("MINIO_BUCKET", "adventureworks-raw")
    run_id = get_ingestion_run_id()
    minio_client = create_minio_client()
    ensure_versioned_bucket(minio_client, bucket_name)
    print(f"MinIO disponível. Bucket versionado: {bucket_name}.")

    with create_connection("SOURCE") as source_conn:
        with create_connection("WAREHOUSE") as warehouse_conn:
            print("Conexões estabelecidas.")

            with warehouse_conn.cursor() as cursor:
                cursor.execute(
                    "CREATE SCHEMA IF NOT EXISTS raw"
                )

            warehouse_conn.commit()
            print("Schema raw disponível.")

            for schema_name, table_name in SOURCE_TABLES:
                print(f"\nCarregando {schema_name}.{table_name}...")

                try:
                    load_table(
                        source_conn,
                        warehouse_conn,
                        minio_client,
                        bucket_name,
                        run_id,
                        schema_name,
                        table_name,
                    )
                    warehouse_conn.commit()

                except Exception:
                    warehouse_conn.rollback()
                    print(
                        f"Erro ao carregar "
                        f"{schema_name}.{table_name}."
                    )
                    raise

            print(
                "\nCarga full refresh concluída com sucesso. "
                f"Execução preservada no bucket {bucket_name}: {run_id}."
            )


if __name__ == "__main__":
    main()
