import io
import os
import tempfile
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pyarrow.parquet as pq

from python.ingestion.load_raw import (
    build_object_name,
    ensure_versioned_bucket,
    export_table_to_parquet,
    get_ingestion_run_id,
    upload_snapshot,
)


class LoadRawMinioTests(unittest.TestCase):
    def test_build_object_name_partitions_parquet_by_table_and_date(self):
        loaded_at = datetime(2026, 8, 13, 22, 30, tzinfo=timezone.utc)

        object_name = build_object_name(
            loaded_at,
            "salesorderheader",
        )

        self.assertEqual(
            object_name,
            "raw/sales_order_header/load_date=2026-08-13/"
            "sales_order_header.parquet",
        )

    @patch.dict(os.environ, {"INGESTION_RUN_ID": "manual:run/01"})
    def test_get_ingestion_run_id_preserves_orchestrator_identifier(self):
        self.assertEqual(get_ingestion_run_id(), "manual:run/01")

    def test_ensure_versioned_bucket_creates_missing_bucket(self):
        client = Mock()
        client.bucket_exists.return_value = False

        ensure_versioned_bucket(client, "adventureworks-raw")

        client.make_bucket.assert_called_once_with("adventureworks-raw")
        client.set_bucket_versioning.assert_called_once()

    def test_export_table_writes_parquet_with_ingestion_metadata(self):
        cursor = Mock()
        cursor.__enter__ = Mock(return_value=cursor)
        cursor.__exit__ = Mock(return_value=False)
        cursor.fetchall.return_value = [(1, "Ada")]
        connection = Mock()
        connection.cursor.return_value = cursor
        loaded_at = datetime(2026, 8, 13, 22, 30, tzinfo=timezone.utc)

        with tempfile.SpooledTemporaryFile(mode="w+b") as snapshot:
            row_count = export_table_to_parquet(
                connection,
                "sales",
                "customer",
                [("customerid", "integer"), ("name", "text")],
                loaded_at,
                snapshot,
            )
            table = pq.read_table(snapshot)

        self.assertEqual(row_count, 1)
        self.assertEqual(table.column_names, [
            "customerid",
            "name",
            "_loaded_at",
            "_source_table",
        ])
        self.assertEqual(table["customerid"].to_pylist(), [1])
        self.assertEqual(
            table["_source_table"].to_pylist(),
            ["sales.customer"],
        )

    def test_upload_snapshot_rewinds_file_and_adds_metadata(self):
        client = Mock()
        client.put_object.return_value = SimpleNamespace(version_id="v1")
        snapshot = io.BytesIO(b"id,name\n1,Ada\n")
        loaded_at = datetime(2026, 8, 13, 22, 30, tzinfo=timezone.utc)

        version_id, snapshot_size = upload_snapshot(
            client,
            "adventureworks-raw",
            "raw/customer/load_date=2026-08-13/customer.parquet",
            "20260813T223000",
            "sales.customer",
            1,
            loaded_at,
            snapshot,
        )

        self.assertEqual(version_id, "v1")
        self.assertEqual(snapshot_size, len(snapshot.getvalue()))
        self.assertEqual(snapshot.tell(), 0)
        call = client.put_object.call_args.kwargs
        self.assertEqual(call["length"], len(snapshot.getvalue()))
        self.assertEqual(
            call["content_type"],
            "application/vnd.apache.parquet",
        )
        self.assertEqual(call["metadata"]["row-count"], "1")
        self.assertEqual(call["metadata"]["source-table"], "sales.customer")
        self.assertEqual(call["metadata"]["run-id"], "20260813T223000")


if __name__ == "__main__":
    unittest.main()
