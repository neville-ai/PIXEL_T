"""Progress reporting for background analysis pipelines.

Extracted from ``analysis_service`` (refactoring stage 1) so that progress
accounting has a single responsibility. The public interface is unchanged:
``AnalysisProgressReporter`` is still importable from both this module and the
historical ``src.services.analysis_service`` location.
"""
from datetime import datetime, timezone
from typing import Optional

from ai.inference.pipeline import PHASE_INFERENCE

# progress_percent = floor(completed_units / total_units * 100), where a unit is
# one completed reportable phase (the 5 pipeline phases + the service-side
# artifact-upload phase) or one completed inference forward pass. This is
# countable completed work, never elapsed time or assumed durations.
_PROGRESS_FLOOR = 100.0

# DB-write throttle: emit an inference progress update roughly every this many
# completed forward passes, in addition to the once-per-phase updates. Keeps
# write volume bounded during the ~25-pass TTA loop.
_PROGRESS_PASS_THROTTLE = 5


class AnalysisProgressReporter:
    """Turn completed pipeline units into throttled DB progress writes.

    Progress is ``floor(completed_units / total_units * 100)`` over countable
    work: one unit per completed pipeline phase, plus one per completed
    inference forward pass. ``current_step`` always reflects the most recently
    completed phase.

    Safety properties:
    - ``progress_percent`` never decreases (writes are skipped when the rounded
      percent has not moved, and the service clamps the stored value).
    - A DB/reporting failure is swallowed and counted (``failed_writes``) but
      never propagates, so a successful AI pipeline is never turned into a
      failure by a progress write.
    - The percentage is capped below 100 (``percent``) so 100% is reserved for
      the final persisted 'completed' state.
    """

    def __init__(self, repository, analysis_id: str, user_id: str,
                 total_units: int, throttle: int = _PROGRESS_PASS_THROTTLE):
        self._repository = repository
        self._analysis_id = analysis_id
        self._user_id = user_id
        self.total_units = max(1, total_units)
        self._throttle = max(1, throttle)
        self._completed_units = 0
        self._passes_done = 0
        self._last_percent = -1
        self._last_step: Optional[str] = None
        self.failed_writes = 0

    @property
    def last_step(self) -> Optional[str]:
        """Most recently completed phase, or None if no phase completed yet."""
        return self._last_step

    @property
    def completed_units(self) -> int:
        return self._completed_units

    @property
    def percent(self) -> int:
        """Completed-work percentage, capped below 100 (100% is 'completed' only)."""
        raw = int(self._completed_units * _PROGRESS_FLOOR / self.total_units)
        return min(raw, 99)

    def on_phase(self, step: str) -> None:
        """Record one completed pipeline phase and report it."""
        self._completed_units += 1
        self._last_step = step
        self._write(step)

    def on_pass(self) -> None:
        """Record one completed inference forward pass; throttle DB writes."""
        self._completed_units += 1
        self._passes_done += 1
        if self._passes_done % self._throttle == 0:
            # Forward passes execute inside the inference stage, so report that
            # stage as running (APIContract: "Tahap yang sedang berjalan, mis.
            # inference"). The unit counted above is a *completed* pass only.
            self._write(PHASE_INFERENCE)

    def _write(self, step: str) -> None:
        percent = self.percent
        # Skip no-op writes (same step, same rounded percent) to keep volume low.
        if step == self._last_step and percent == self._last_percent:
            return
        try:
            self._repository.update(
                analysis_id=self._analysis_id,
                user_id=self._user_id,
                data={
                    "current_step": step,
                    "progress_percent": percent,
                    # The migration does not auto-update updated_at.
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                },
                use_service_role=True,
            )
            self._last_percent = percent
        except Exception:
            # Reporting failure != inference failure. Count it, keep going, and
            # never let it abort a safe, successful pipeline.
            self.failed_writes += 1
