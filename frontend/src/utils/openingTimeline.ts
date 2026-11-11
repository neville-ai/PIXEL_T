/**
 * Single source of truth for the PIXEL-T Opening Animation timeline.
 *
 * The timeline is the approved 10-stage, nominal 10 second specification.
 * All values are deterministic constants — no randomness, no scattered timings.
 */

export const OPENING_STAGES = [
  'initial',
  'focalPixelFormation',
  'supportingPixels',
  'segmentationFrame',
  'completeLogo',
  'identityMoment',
  'logoTransition',
  'loginUiReveal',
  'layoutSettlement',
  'finalHold',
] as const;

export type OpeningStage = (typeof OPENING_STAGES)[number];

/** Start time (ms, cumulative from 0) of each stage. */
export const OPENING_STAGE_START_MS: Record<OpeningStage, number> = {
  initial: 0,
  focalPixelFormation: 700,
  supportingPixels: 1600,
  segmentationFrame: 2500,
  completeLogo: 3300,
  identityMoment: 4000,
  logoTransition: 6000,
  loginUiReveal: 7000,
  layoutSettlement: 8200,
  finalHold: 9000,
};

/** Nominal total duration of the opening animation. */
export const OPENING_TOTAL_DURATION_MS = 10000;

/**
 * Versioned sessionStorage key. Bump the version if the playback rule changes
 * so older flags are naturally ignored.
 */
export const OPENING_SESSION_STORAGE_KEY = 'pixel-t-intro-played-v1';

/** localStorage key for the "Remember my email" preference (e-mail only). */
export const REMEMBERED_EMAIL_STORAGE_KEY = 'pixel-t-remembered-email-v1';

/** Zero-based index of a stage within the timeline. */
export function stageIndex(stage: OpeningStage): number {
  return OPENING_STAGES.indexOf(stage);
}

/** Deterministic stage lookup for an elapsed time in milliseconds. */
export function stageAtElapsed(elapsedMs: number): OpeningStage {
  const clamped = Math.max(0, elapsedMs);
  let current: OpeningStage = OPENING_STAGES[0];
  for (const stage of OPENING_STAGES) {
    if (clamped >= OPENING_STAGE_START_MS[stage]) {
      current = stage;
    } else {
      break;
    }
  }
  return current;
}

/*
 * In-memory fallback used only when sessionStorage itself is unavailable
 * (e.g. private browsing restrictions). Never breaks the Login page.
 */
let playedInMemory = false;

/**
 * Timestamp of the last time the opening component unmounted.
 * Used to distinguish a React StrictMode/dev double-mount (same tick)
 * from a genuine revisit to /login later in the session.
 */
let lastOpeningUnmountAt = 0;

/** StrictMode remounts happen synchronously; anything larger is a real revisit. */
const STRICT_REMOUNT_WINDOW_MS = 250;

/** Records that the opening component unmounted (called from effect cleanup). */
export function noteOpeningUnmount(now: number = Date.now()): void {
  lastOpeningUnmountAt = now;
}

/** Whether the intro has already been played, safely across storage failures. */
export function hasOpeningPlayed(): boolean {
  try {
    if (typeof window !== 'undefined' && window.sessionStorage) {
      const stored = window.sessionStorage.getItem(OPENING_SESSION_STORAGE_KEY);
      if (stored !== null) {
        return stored === '1';
      }
    }
  } catch {
    // Storage may throw in restricted contexts — fall back to memory.
  }
  return playedInMemory;
}

/**
 * Marks the intro as played as early as playback starts, so a failed Login
 * attempt or any later remount in the same tab never replays the intro.
 * Storage failures are swallowed — Login must keep working regardless.
 */
export function markOpeningPlayed(): void {
  playedInMemory = true;
  try {
    if (typeof window !== 'undefined' && window.sessionStorage) {
      window.sessionStorage.setItem(OPENING_SESSION_STORAGE_KEY, '1');
    }
  } catch {
    // Ignore: in-memory flag still prevents replays for this page load.
  }
}

/**
 * Decides whether the opening animation should play for the current mount.
 *
 * - First visit in this tab session -> play.
 * - Already played (reload, revisit, logout -> /login) -> skip.
 * - Exception: an immediate remount within the strict-remount window
 *   (React StrictMode dev double-mount) -> play, so the timeline restarts
 *   cleanly instead of being swallowed by our own early flag.
 */
export function shouldPlayIntro(now: number = Date.now()): boolean {
  if (!hasOpeningPlayed()) {
    return true;
  }
  if (lastOpeningUnmountAt > 0 && now - lastOpeningUnmountAt < STRICT_REMOUNT_WINDOW_MS) {
    return true;
  }
  return false;
}

/** True when the user prefers reduced motion. Safe when matchMedia is missing. */
export function prefersReducedMotion(): boolean {
  try {
    if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }
  } catch {
    // Ignore: treat as "no preference".
  }
  return false;
}

/** Reads the remembered e-mail for the "Remember my email" checkbox. Never throws. */
export function getRememberedEmail(): string | null {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      return window.localStorage.getItem(REMEMBERED_EMAIL_STORAGE_KEY);
    }
  } catch {
    // Ignore: Login works without prefill.
  }
  return null;
}

/** Persists (or clears) the remembered e-mail. Never throws. Never stores passwords. */
export function setRememberedEmail(email: string | null): void {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      if (email === null) {
        window.localStorage.removeItem(REMEMBERED_EMAIL_STORAGE_KEY);
      } else {
        window.localStorage.setItem(REMEMBERED_EMAIL_STORAGE_KEY, email);
      }
    }
  } catch {
    // Ignore: storage may be unavailable; Login still functions.
  }
}
