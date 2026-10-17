import { useEffect, useState } from 'react';
import {
  OPENING_STAGE_START_MS,
  OPENING_STAGES,
  OPENING_TOTAL_DURATION_MS,
  markOpeningPlayed,
  noteOpeningUnmount,
  prefersReducedMotion,
  shouldPlayIntro,
  type OpeningStage,
} from '@/lib/openingTimeline';

export interface UseOpeningAnimationResult {
  /** Current timeline stage; `finalHold` when skipped or finished. */
  stage: OpeningStage;
  /** Whether the opening overlay should stay mounted and driving the page. */
  isActive: boolean;
  /** True once the timeline has finished (or was skipped entirely). */
  isDone: boolean;
}

/**
 * Deterministic state machine for the 10-stage, nominal 10s opening animation.
 *
 * - One sequential `setTimeout` chain per mount; never an interval, never a
 *   requestAnimationFrame loop, and never a per-frame React state update.
 * - The play/skip decision in `useState` is a PURE read (`shouldPlayIntro`
 *   without marking), so React StrictMode's double-invoked initializer always
 *   reaches the same result — no accidental skip, no accidental replay.
 * - The "played" session flag is marked at the top of the mount effect, i.e.
 *   as early as playback starts and always before any timer fires, so a
 *   failed Login attempt never replays the intro.
 * - All timers are cleared on unmount (plus a `noteOpeningUnmount` marker that
 *   lets an immediate dev-only remount restart cleanly while a genuine later
 *   revisit skips), so two timelines can never run concurrently.
 * - Reduced-motion users skip the long sequence (but still record playback)
 *   and land on the final layout.
 * - If scheduling throws for any reason, the machine falls straight to the
 *   final state so Login is never trapped behind a broken animation.
 */
export function useOpeningAnimation(): UseOpeningAnimationResult {
  // Pure decision — safe to invoke twice under StrictMode.
  const [shouldPlay] = useState<boolean>(() => {
    if (prefersReducedMotion()) {
      // Idempotent: recording here does not influence this decision.
      markOpeningPlayed();
      return false;
    }
    return shouldPlayIntro();
  });

  const [stage, setStage] = useState<OpeningStage>(shouldPlay ? 'initial' : 'finalHold');
  const [isDone, setIsDone] = useState<boolean>(!shouldPlay);

  useEffect(() => {
    if (!shouldPlay) {
      return;
    }

    // Record playback as early as it starts (before any timer can fire).
    markOpeningPlayed();

    const timeouts: number[] = [];
    try {
      // Sequential chain: initial -> focalPixelFormation -> ... -> finalHold.
      for (const nextStage of OPENING_STAGES.slice(1)) {
        timeouts.push(
          window.setTimeout(() => setStage(nextStage), OPENING_STAGE_START_MS[nextStage])
        );
      }
      // Completion marker at the nominal 10s boundary.
      timeouts.push(window.setTimeout(() => setIsDone(true), OPENING_TOTAL_DURATION_MS));
    } catch {
      // Safety fallback: never leave the user behind a broken timeline.
      setStage('finalHold');
      setIsDone(true);
    }

    return () => {
      timeouts.forEach((id) => window.clearTimeout(id));
      noteOpeningUnmount();
    };
  }, [shouldPlay]);

  return { stage, isActive: shouldPlay && !isDone, isDone };
}

export default useOpeningAnimation;
