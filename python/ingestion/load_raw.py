import os
from datetime import datetime, timezone

import psycopg
from psycopg import sql
from dotenv import load_dotenv


load_dotenv()


SOURCE_TABLES = [
    ("sales", "salesorderheader"),
    ("sales", "salesorderdetail"),
    ("sales", "customer"),
    ("sales", "salesterritory"),
    ("sales", "store"),
    ("production", "product"),
    ("person", "person"),
]


def create_connection(prefix: str) -> psycopg.Connection:
    return psycopg.connect(
        host="localhost",
        dbname=os.environ[f"{prefix}_DB_NAME"],
        user=os.environ[f"{prefix}_DB_USER"],
        password=os.environ[f"{prefix}_DB_PASSWORD"],
        port=os.environ[f"{prefix}_DB_PORT"],
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


def load_table(
    source_conn: psycopg.Connection,
    warehouse_conn: psycopg.Connection,
    schema_name: str,
    table_name: str,
) -> int:
    columns = get_columns(
        source_conn,
        schema_name,
        table_name,
    )

    recreate_raw_table(
        warehouse_conn,
        table_name,
        columns,
    )

    column_names = [column_name for column_name, _ in columns]

    select_query = sql.SQL("SELECT {} FROM {}.{}").format(
        sql.SQL(", ").join(map(sql.Identifier, column_names)),
        sql.Identifier(schema_name),
        sql.Identifier(table_name),
    )

    insert_query = sql.SQL(
        "INSERT INTO raw.{} ({}, _loaded_at, _source_table) "
        "VALUES ({}, %s, %s)"
    ).format(
        sql.Identifier(table_name),
        sql.SQL(", ").join(map(sql.Identifier, column_names)),
        sql.SQL(", ").join(sql.Placeholder() * len(column_names)),
    )

    loaded_at = datetime.now(timezone.utc)
    source_table = f"{schema_name}.{table_name}"
    row_count = 0
    batch_size = 5_000

    with source_conn.cursor() as source_cursor:
        source_cursor.execute(select_query)

        with warehouse_conn.cursor() as warehouse_cursor:
            while rows := source_cursor.fetchmany(batch_size):
                records = [
                    (*row, loaded_at, source_table)
                    for row in rows
                ]

                warehouse_cursor.executemany(
                    insert_query,
                    records,
                )

                row_count += len(records)
                print(
                    f"  {source_table}: "
                    f"{row_count:,} registros copiados",
                    end="\r",
                )

    print(
        f"  {source_table}: "
        f"{row_count:,} registros copiados"
    )

    return row_count


def main() -> None:
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

            print("\nCarga full refresh concluída com sucesso.")


if __name__ == "__main__":
    main()