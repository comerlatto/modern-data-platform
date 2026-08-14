import sys
import types
import unittest
from pathlib import Path


psycopg = types.ModuleType("psycopg")
psycopg.Connection = object
psycopg.sql = types.SimpleNamespace()
psycopg.rows = types.ModuleType("psycopg.rows")
psycopg.rows.dict_row = object()
psycopg.types = types.ModuleType("psycopg.types")
psycopg.types.json = types.ModuleType("psycopg.types.json")
psycopg.types.json.Jsonb = lambda value, **kwargs: value
sys.modules.setdefault("psycopg", psycopg)
sys.modules.setdefault("psycopg.rows", psycopg.rows)
sys.modules.setdefault("psycopg.types", psycopg.types)
sys.modules.setdefault("psycopg.types.json", psycopg.types.json)

sys.path.insert(0, str(Path(__file__).parents[1]))

from python.observability.load_dbt_artifacts import integer_or_none


class DbtArtifactTests(unittest.TestCase):
    def test_integer_or_none_converts_dbt_failure_counts(self):
        self.assertEqual(integer_or_none("3"), 3)
        self.assertEqual(integer_or_none(0), 0)
        self.assertIsNone(integer_or_none(None))
        self.assertIsNone(integer_or_none(True))
        self.assertIsNone(integer_or_none("invalid"))


if __name__ == "__main__":
    unittest.main()
