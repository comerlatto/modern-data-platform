"""Pure domain rules shared by the observability API and its tests."""

from __future__ import annotations


def normalize_status(value: str | None) -> str:
    status = (value or "not_started").lower()
    if status in {"success", "pass", "passed"}:
        return "success"
    if status in {"warn", "warning"}:
        return "warning"
    if status in {"error", "fail", "failed", "runtime error"}:
        return "failed"
    if status in {"running", "started"}:
        return "running"
    if status == "blocked":
        return "blocked"
    if status in {"skipped", "not_applicable"}:
        return "not_applicable"
    if status in {"unmonitored", "not_monitored"}:
        return "unmonitored"
    return "not_started"


def aggregate_status(statuses: list[str], has_evidence: bool = True) -> str:
    values = {normalize_status(status) for status in statuses}
    applicable = values - {"not_applicable"}
    if "failed" in applicable:
        return "failed"
    if "running" in applicable:
        return "running"
    if "warning" in applicable or "blocked" in applicable:
        return "warning"
    if not has_evidence or not applicable or applicable <= {"not_started", "unmonitored"}:
        return "not_started"
    return "success" if applicable == {"success"} else "warning"


def trigger_type(run_id: str | None) -> str | None:
    if not run_id:
        return None
    if run_id.startswith("manual__"):
        return "manual"
    if run_id.startswith(("scheduled__", "backfill__")):
        return "scheduled"
    return "other"
