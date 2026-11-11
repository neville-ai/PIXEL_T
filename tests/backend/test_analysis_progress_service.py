"""Focused tests for the extracted AnalysisProgressReporter (refactoring stage 1).

Covers the mandatory refactoring contract items: monotonic percent based on
completed units, sub-100 cap until completion, best-effort writes (failure is
counted and swallowed, never fatal), throttling, and the import contract.
"""
from src.services.analysis_progress_service import AnalysisProgressReporter


class RecordingRepository:
    """Fake persistence surface used by the reporter."""

    def __init__(self, fail_writes: bool = False):
        self.writes: list[dict] = []
        self.fail_writes = fail_writes

    def update(self, analysis_id: str, user_id: str, data: dict,
               use_service_role: bool = False) -> dict:
        if self.fail_writes:
            raise RuntimeError("simulated progress write failure")
        self.writes.append(dict(data))
        return {"id": analysis_id, "status": "processing"}


def _make_reporter(total_units: int = 10, throttle: int = 5,
                   fail_writes: bool = False) -> tuple:
    repository = RecordingRepository(fail_writes=fail_writes)
    reporter = AnalysisProgressReporter(
        repository=repository,
        analysis_id="analysis-1",
        user_id="user-a",
        total_units=total_units,
        throttle=throttle,
    )
    return reporter, repository


def test_percent_is_monotonic_and_derived_from_completed_units():
    reporter, repository = _make_reporter(total_units=10)
    observed = [reporter.percent]
    for _ in range(10):
        reporter.on_phase("inference")
        observed.append(reporter.percent)

    assert reporter.completed_units == 10
    # 100% is reserved for the final 'completed' state.
    assert reporter.percent == 99
    assert observed == sorted(observed)
    assert reporter.last_step == "inference"
    assert [write["progress_percent"] for write in repository.writes] == sorted(
        write["progress_percent"] for write in repository.writes
    )


def test_percent_never_reaches_100_before_completion():
    reporter, repository = _make_reporter(total_units=2)
    for _ in range(10):
        reporter.on_phase("inference")

    assert reporter.percent == 99
    assert all(write["progress_percent"] <= 99
               for write in repository.writes)


def test_failed_progress_write_is_counted_and_swallowed():
    reporter, repository = _make_reporter(total_units=4, fail_writes=True)

    for step in ("preprocessing", "inference", "segmentation"):
        reporter.on_phase(step)

    # Reporting failure never propagates, but is counted so it can be audited.
    assert reporter.failed_writes == 3
    assert reporter.completed_units == 3
    assert reporter.last_step == "segmentation"
    assert repository.writes == []  # nothing landed in the DB


def test_pass_writes_are_throttled_by_throttle_value():
    reporter, repository = _make_reporter(total_units=100, throttle=5)

    for _ in range(12):
        reporter.on_pass()

    assert reporter.completed_units == 12
    # One DB write per completed batch of `throttle` forward passes.
    assert len(repository.writes) == 2


def test_write_payload_carries_step_percent_and_updated_at():
    reporter, repository = _make_reporter(total_units=8)

    reporter.on_phase("preprocessing")
    write = repository.writes[-1]

    assert write["current_step"] == "preprocessing"
    assert write["progress_percent"] == 12  # floor(1 * 100 / 8)
    assert write["updated_at"]


def test_public_reexport_from_analysis_service_still_works():
    from src.services.analysis_service import (
        AnalysisProgressReporter as ReporterReexport,
    )
    from src.services.analysis_progress_service import AnalysisProgressReporter

    assert ReporterReexport is AnalysisProgressReporter
