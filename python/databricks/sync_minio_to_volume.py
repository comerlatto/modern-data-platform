import argparse
import os
from pathlib import PurePosixPath

from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv
from minio import Minio


DEFAULT_VOLUME_PATH = (
    "/Volumes/workspace/bronze/adventureworks_files"
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sincroniza os snapshots Parquet mais recentes do MinIO "
            "com um Volume do Databricks."
        )
    )
    parser.add_argument(
        "--table",
        action="append",
        help=(
            "Nome da tabela no MinIO. Pode ser informado mais de uma vez. "
            "Sem esse argumento, todas as tabelas serão sincronizadas."
        ),
    )
    return parser.parse_args()


def env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in {
        "1",
        "true",
        "yes",
    }


def create_minio_client() -> Minio:
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
        secure=env_flag("MINIO_SECURE"),
    )


def get_latest_snapshots(
    client: Minio,
    bucket_name: str,
    selected_tables: list[str] | None,
) -> dict[str, object]:
    latest_by_table = {}

    for item in client.list_objects(
        bucket_name,
        prefix="raw/",
        recursive=True,
    ):
        path_parts = PurePosixPath(item.object_name).parts

        if len(path_parts) < 4:
            continue

        if path_parts[0] != "raw":
            continue

        if not item.object_name.endswith(".parquet"):
            continue

        table_name = path_parts[1]

        if selected_tables and table_name not in selected_tables:
            continue

        current = latest_by_table.get(table_name)

        if current is None or item.last_modified > current.last_modified:
            latest_by_table[table_name] = item

    return latest_by_table


def upload_snapshot(
    minio_client: Minio,
    databricks_client: WorkspaceClient,
    bucket_name: str,
    volume_path: str,
    table_name: str,
    object_name: str,
) -> None:
    remote_directory = f"{volume_path}/raw/{table_name}"
    remote_file = f"{remote_directory}/{PurePosixPath(object_name).name}"

    databricks_client.files.create_directory(remote_directory)

    response = minio_client.get_object(
        bucket_name,
        object_name,
    )

    try:
        databricks_client.files.upload(
            remote_file,
            response,
            overwrite=True,
            use_parallel=False,
        )
    finally:
        response.close()
        response.release_conn()

    print(
        f"Sincronizado: {bucket_name}/{object_name} "
        f"-> {remote_file}"
    )


def main() -> None:
    load_dotenv()
    args = parse_arguments()

    bucket_name = os.getenv(
        "MINIO_BUCKET",
        "adventureworks-raw",
    )
    volume_path = os.getenv(
        "DATABRICKS_VOLUME_PATH",
        DEFAULT_VOLUME_PATH,
    )
    profile = os.getenv(
        "DATABRICKS_CONFIG_PROFILE",
        "modern-data-platform",
    )

    minio_client = create_minio_client()
    databricks_client = WorkspaceClient(profile=profile)

    snapshots = get_latest_snapshots(
        minio_client,
        bucket_name,
        args.table,
    )

    if not snapshots:
        raise RuntimeError(
            "Nenhum snapshot Parquet correspondente foi encontrado."
        )

    for table_name, snapshot in sorted(snapshots.items()):
        upload_snapshot(
            minio_client=minio_client,
            databricks_client=databricks_client,
            bucket_name=bucket_name,
            volume_path=volume_path,
            table_name=table_name,
            object_name=snapshot.object_name,
        )

    print(
        f"Sincronização concluída: {len(snapshots)} arquivo(s)."
    )


if __name__ == "__main__":
    main()