"""Focused tests for the extracted AnalysisJobQueue (refactoring stage 1).

Covers the mandatory refactoring contract items that are unit-testable at the
queue level: FIFO, active-job-aware capacity, drain_one determinism, and worker
resilience. Service-level behaviour stays covered by the existing
``tests/backend/test_analysis.py`` suite.
"""
import logging
import threading
import time

from src.services.analysis_queue_service import AnalysisJobQueue


def _job(analysis_id: str) -> dict:
    return {"analysis_id": analysis_id}


def _wait_until(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return bool(predicate())


def test_queue_preserves_fifo_order():
    order: list[str] = []
    queue = AnalysisJobQueue(
        runner=lambda job: order.append(job["analysis_id"]),
        auto_start=False,
    )
    for name in ("a", "b", "c"):
        assert queue.try_enqueue(_job(name)) is True

    while queue.drain_one():
        pass

    assert order == ["a", "b", "c"]
    assert queue.pending_count() == 0


def test_drain_one_is_deterministic_and_empty_queue_returns_false():
    queue = AnalysisJobQueue(runner=lambda job: None, auto_start=False)

    assert queue.drain_one() is False

    assert queue.try_enqueue(_job("only")) is True
    assert queue.drain_one() is True
    assert queue.drain_one() is False
    assert queue.pending_count() == 0


def test_full_queue_is_rejected_and_capacity_is_recovered_after_completion():
    queue = AnalysisJobQueue(runner=lambda job: None, auto_start=False)

    for i in range(queue.capacity):
        assert queue.try_enqueue(_job(f"job-{i}")) is True
    assert queue.try_enqueue(_job("overflow")) is False
    assert queue.pending_count() == queue.capacity

    assert queue.drain_one() is True
    # The in-flight slot was released once the job finished, so capacity is
    # available again.
    assert queue.pending_count() == queue.capacity - 1
    assert queue.try_enqueue(_job("job-next")) is True
    assert queue.pending_count() == queue.capacity


def test_capacity_counts_active_job_and_caps_waiting_jobs():
    release = threading.Event()
    started = threading.Event()
    queue = AnalysisJobQueue(
        runner=lambda job: (started.set(), release.wait(timeout=5)),
        auto_start=True,
    )

    try:
        assert queue.try_enqueue(_job("active")) is True
        # The worker picked the job up: exactly one job is now in flight.
        assert started.wait(timeout=5) is True

        # 1 active + up to MAX_WAITING waiting is allowed; no more is accepted.
        assert queue.try_enqueue(_job("wait-1")) is True
        assert queue.try_enqueue(_job("wait-2")) is True
        assert queue.try_enqueue(_job("wait-3")) is True
        assert queue.try_enqueue(_job("overflow")) is False
        assert queue.pending_count() == AnalysisJobQueue.MAX_WAITING
    finally:
        release.set()

    assert _wait_until(lambda: not queue.contains("wait-3"))
    assert queue.contains("active") is False


def test_contains_covers_active_and_waiting_jobs():
    release = threading.Event()
    started = threading.Event()
    queue = AnalysisJobQueue(
        runner=lambda job: (started.set(), release.wait(timeout=5)),
        auto_start=True,
    )

    try:
        assert queue.try_enqueue(_job("active")) is True
        assert started.wait(timeout=5) is True
        assert queue.try_enqueue(_job("waiting")) is True

        assert queue.contains("active") is True
        assert queue.contains("waiting") is True
        assert queue.contains("unknown-id") is False
    finally:
        release.set()

    assert _wait_until(lambda: not queue.contains("waiting"))
    assert queue.contains("active") is False


def test_drain_one_refuses_to_run_while_worker_is_running():
    release = threading.Event()
    started = threading.Event()
    queue = AnalysisJobQueue(
        runner=lambda job: (started.set(), release.wait(timeout=5)),
        auto_start=True,
    )

    try:
        assert queue.try_enqueue(_job("active")) is True
        assert started.wait(timeout=5) is True
        assert queue.try_enqueue(_job("waiting")) is True
        # The worker thread owns the in-flight slot: drain_one must not start a
        # second job while one is already running.
        assert queue.drain_one() is False
    finally:
        release.set()

    assert _wait_until(lambda: queue.pending_count() == 0)
    assert queue.contains("active") is False


def test_worker_survives_runner_exception_and_continues_processing(caplog):
    finished = threading.Event()
    order: list[str] = []

    def runner(job: dict) -> None:
        if job["analysis_id"] == "boom":
            raise RuntimeError("simulated runner failure")
        order.append(job["analysis_id"])
        finished.set()

    queue = AnalysisJobQueue(runner=runner, auto_start=True)

    with caplog.at_level(logging.ERROR):
        assert queue.try_enqueue(_job("boom")) is True
        assert queue.try_enqueue(_job("ok")) is True
        assert finished.wait(timeout=5) is True

    # The worker kept going and never died.
    assert order == ["ok"]
    assert any("Worker exception" in record.getMessage() for record in caplog.records)


def test_only_one_job_runs_at_a_time_across_worker_and_drain():
    lock = threading.Lock()
    state = {"active": 0, "max_active": 0}
    order: list[str] = []

    def runner(job: dict) -> None:
        with lock:
            state["active"] += 1
            state["max_active"] = max(state["max_active"], state["active"])
        time.sleep(0.005)
        with lock:
            order.append(job["analysis_id"])
            state["active"] -= 1

    queue = AnalysisJobQueue(runner=runner, auto_start=True)
    accepted_ids: list[str] = []
    for i in range(10):
        if queue.try_enqueue(_job(f"job-{i}")):
            accepted_ids.append(f"job-{i}")

    deadline = time.monotonic() + 5
    while time.monotonic() < deadline and (queue.pending_count() != 0 or state["active"] != 0):
        queue.drain_one()
        time.sleep(0.001)

    assert _wait_until(lambda: queue.pending_count() == 0 and state["active"] == 0)
    assert len(accepted_ids) <= queue.capacity
    # Even with drain_one interleaved with the worker, never more than one job
    # runs at a time.
    assert state["max_active"] == 1


def test_public_reexport_from_analysis_service_still_works():
    from src.services.analysis_service import (
        AnalysisJobQueue as QueueReexport,
    )
    from src.services.analysis_queue_service import AnalysisJobQueue

    assert QueueReexport is AnalysisJobQueue
