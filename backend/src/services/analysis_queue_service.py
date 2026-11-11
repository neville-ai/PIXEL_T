"""In-memory FIFO queue for background analysis pipelines (stdlib only).

Extracted from ``analysis_service`` (refactoring stage 1) so that queueing has
a single responsibility. The public interface is unchanged: ``AnalysisJobQueue``
is still importable from both this module and the historical
``src.services.analysis_service`` location.

Capacity contract (fixed during the extraction):
- At most one job may be active at a time.
- At most ``MAX_WAITING`` jobs may wait behind the active job.
- Total accepted jobs (active + waiting) never exceed ``MAX_WAITING + 1``.
- When full, ``try_enqueue`` returns ``False`` so the caller can return 429.
"""
import logging
import threading
import time
from collections import deque
from typing import Any, Callable, Deque, Dict, Optional

logger = logging.getLogger(__name__)


class AnalysisJobQueue:
    """In-memory FIFO queue for background analysis pipelines (stdlib only).

    Capacity: the queue accepts at most ``MAX_WAITING + 1`` jobs in total. A
    single worker thread runs one job at a time; up to ``MAX_WAITING`` additional
    jobs wait behind it. When full, ``try_enqueue`` returns ``False`` so the
    caller can return HTTP 429.

    The capacity check counts the in-flight job (``_active_analysis_id``) as
    well, so the accepted total never exceeds the limit. The check and the
    append happen atomically under the same lock.

    Limitations (documented, not hidden):
    - The queue is in-memory and per-process. A process restart loses every
      queued and in-flight job; the affected record stays at 'processing'
      until inspected (see the non-mutating stale marker in ``get_analysis``).
    - Exactly-once execution holds for the normal queue lifecycle (each job is
      popped once). There is no retry and no cross-process coordination.
    - The worker thread is a daemon thread; it will be terminated when the
      main process exits. Use ``shutdown()`` to attempt a controlled stop.
    """

    MAX_WAITING = 3

    def __init__(
        self,
        runner: Callable[[Dict[str, Any]], None],
        max_waiting: int = MAX_WAITING,
        auto_start: bool = True,
    ):
        self._runner = runner
        self._max_waiting = max_waiting
        self._jobs: Deque[Dict[str, Any]] = deque()
        self._lock = threading.Lock()
        self._not_empty = threading.Condition(self._lock)
        self._worker_started = False
        self._auto_start = auto_start
        self._active_analysis_id: Optional[str] = None
        # Graceful-shutdown signal (thread-safe, stdlib only).
        self._shutdown_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None

    @property
    def capacity(self) -> int:
        """Total jobs the queue accepts before reporting full (1 + MAX_WAITING)."""
        return self._max_waiting + 1

    # ------------------------------------------------------------------
    # Public read-only status
    # ------------------------------------------------------------------

    @property
    def is_shutdown_requested(self) -> bool:
        """True once ``shutdown()`` has been called."""
        return self._shutdown_event.is_set()

    @property
    def worker_alive(self) -> bool:
        """True while the worker thread is still running."""
        t = self._worker_thread
        return t is not None and t.is_alive()

    def try_enqueue(self, job: Dict[str, Any]) -> bool:
        """Enqueue a job, returning False when the queue is at capacity."""
        if self._shutdown_event.is_set():
            return False
        job_with_time = dict(job)
        job_with_time["enqueued_at"] = time.perf_counter()
        with self._not_empty:
            in_flight = 1 if self._active_analysis_id is not None else 0
            if len(self._jobs) + in_flight >= self.capacity:
                return False
            self._jobs.append(job_with_time)
            self._not_empty.notify()
        if self._auto_start:
            self._ensure_worker()
        return True

    def contains(self, analysis_id: str) -> bool:
        """True when the job is the active one or still waiting in this process."""
        with self._lock:
            if self._active_analysis_id == analysis_id:
                return True
            return any(job.get("analysis_id") == analysis_id for job in self._jobs)

    def pending_count(self) -> int:
        with self._lock:
            return len(self._jobs)

    def drain_one(self) -> bool:
        """Run exactly one queued job synchronously and return whether one ran.

        Deterministic test hook: avoids threads/sleeps so tests can step the
        queue without race conditions. Refuses to start a second job while one
        is already active so the queue never runs jobs concurrently.
        """
        with self._not_empty:
            if self._active_analysis_id is not None:
                # The worker thread owns the in-flight slot; do not run a second
                # job concurrently with it.
                return False
            if not self._jobs:
                return False
            job = self._jobs.popleft()
            self._active_analysis_id = job.get("analysis_id")
        try:
            self._runner(job)
        finally:
            with self._not_empty:
                self._active_analysis_id = None
                # Wake the worker in case it parked while this job was active.
                self._not_empty.notify()
        return True

    def purge_job(self, analysis_id: str) -> bool:
        """Remove a waiting job by ``analysis_id`` without running it.

        Only jobs still waiting in ``_jobs`` can be purged; the active job
        (``_active_analysis_id``) is owned by the worker and is intentionally
        left untouched so cooperative cancellation can handle it instead.
        All other FIFO jobs keep their relative order. Notifies the worker so
        it can re-evaluate the queue after a purge.
        """
        with self._not_empty:
            for index, job in enumerate(self._jobs):
                if job.get("analysis_id") == analysis_id:
                    self._jobs.remove(job)
                    self._not_empty.notify()
                    return True
            return False

    # ------------------------------------------------------------------
    # Graceful shutdown
    # ------------------------------------------------------------------

    def shutdown(self, join_timeout: float = 30.0) -> None:
        """Signal the worker to stop and optionally wait for it to finish.

        * The worker stops accepting new jobs immediately after this call.
        * If a job is currently running, the worker lets it complete (up to
          ``join_timeout`` seconds) rather than killing it mid-inference.
        * Already-waiting jobs remain in the queue but will not be processed
          after shutdown completes; callers are expected to mark them
          ``failed`` in the database before or during shutdown.
        * This method is idempotent — calling it multiple times is safe.
        """
        self._shutdown_event.set()
        with self._not_empty:
            self._not_empty.notify_all()

        if self._worker_thread is not None and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=join_timeout)
            if self._worker_thread.is_alive():
                logger.warning(
                    "[SHUTDOWN] Worker thread did not finish within %.1fs; "
                    "remaining job(s) will be lost on process exit.",
                    join_timeout,
                )

    def _ensure_worker(self) -> None:
        with self._not_empty:
            if self._worker_started:
                return
            self._worker_started = True
            t = threading.Thread(
                target=self._work_loop, name="analysis-worker", daemon=True
            )
            self._worker_thread = t
            t.start()

    def _work_loop(self) -> None:
        while not self._shutdown_event.is_set():
            job = None
            with self._not_empty:
                while (
                    not self._jobs
                    or self._active_analysis_id is not None
                    or self._shutdown_event.is_set()
                ):
                    if self._shutdown_event.is_set() and self._active_analysis_id is None:
                        # No in-flight job and nothing queued → leave loop.
                        return
                    self._not_empty.wait(timeout=0.5)  # periodic wake for shutdown check
                job = self._jobs.popleft()
                self._active_analysis_id = job.get("analysis_id")
                # Measure queue wait time
                enqueued_at = job.get("enqueued_at")
                if enqueued_at is not None:
                    wait_time = time.perf_counter() - enqueued_at
                    logger.info(f"[TIMING] analysis_id={job.get('analysis_id')} stage=queue_wait duration_ms={wait_time * 1000:.1f}")
            try:
                self._runner(job)
            except Exception as exc:
                # The runner persists its own failures; this guard only keeps
                # the worker alive if an error ever escapes it.
                analysis_id = job.get('analysis_id', 'unknown')
                logger.error(
                    f"[ERROR] Worker exception for analysis_id={analysis_id}: {exc}",
                    exc_info=True,
                )
            finally:
                with self._not_empty:
                    self._active_analysis_id = None
                    self._not_empty.notify()
