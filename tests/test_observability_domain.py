import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[1] / "observability" / "api"))

from domain import aggregate_status, normalize_status, trigger_type


class ObservabilityDomainTests(unittest.TestCase):
    def test_failure_has_precedence(self):
        self.assertEqual(aggregate_status(["success", "failed"]), "failed")

    def test_warning_does_not_become_success(self):
        self.assertEqual(aggregate_status(["success", "warn"]), "warning")

    def test_missing_evidence_is_not_healthy(self):
        self.assertEqual(aggregate_status([], has_evidence=False), "not_started")

    def test_partial_evidence_requires_attention(self):
        self.assertEqual(
            aggregate_status(["success", "success", "not_started"]),
            "warning",
        )

    def test_not_applicable_is_distinct_from_pending(self):
        self.assertEqual(normalize_status("skipped"), "not_applicable")

    def test_trigger_is_derived_from_airflow_run_id(self):
        self.assertEqual(trigger_type("manual__2026-08-14T12:00:00+00:00"), "manual")
        self.assertEqual(trigger_type("scheduled__2026-08-14T12:00:00+00:00"), "scheduled")


if __name__ == "__main__":
    unittest.main()
