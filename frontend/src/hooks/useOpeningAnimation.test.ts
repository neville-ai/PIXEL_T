import { createElement, StrictMode, type ReactNode } from 'react';
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  OPENING_SESSION_STORAGE_KEY,
  OPENING_STAGE_START_MS,
  OPENING_STAGES,
  OPENING_TOTAL_DURATION_MS,
} from '@/lib/openingTimeline';

type HookModule = typeof import('./useOpeningAnimation');

let hook: HookModule;

/**
 * Fresh module per test so the module-level playback marker never leaks
 * between cases (vitest has no global reset for imported module state).
 */
beforeEach(async () => {
  vi.resetModules();
  window.sessionStorage.clear();
  vi.useFakeTimers();
  hook = await import('./useOpeningAnimation');
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

const StrictWrapper = ({ children }: { children: ReactNode }) =>
  createElement(StrictMode, null, children);

describe('useOpeningAnimation — deterministic timeline', () => {
  it('melewati seluruh 10 tahap secara berurutan tanpa melompat, lalu selesai di 10 detik', () => {
    const { result } = renderHook(() => hook.useOpeningAnimation());

    // Fresh session -> intro plays from the first stage.
    expect(result.current.stage).toBe('initial');
    expect(result.current.isActive).toBe(true);
    expect(result.current.isDone).toBe(false);
    // Flag recorded as early as playback starts (before any timer fires).
    expect(window.sessionStorage.getItem(OPENING_SESSION_STORAGE_KEY)).toBe('1');

    const visited: string[] = [result.current.stage];
    let elapsed = 0;
    for (const nextStage of OPENING_STAGES.slice(1)) {
      const target = OPENING_STAGE_START_MS[nextStage];
      act(() => {
        vi.advanceTimersByTime(target - elapsed);
      });
      elapsed = target;
      expect(result.current.stage).toBe(nextStage);
      visited.push(nextStage);
    }

    // Visited exactly the 10 stages, in order — none skipped, none repeated
    // out of order.
    expect(visited).toEqual([...OPENING_STAGES]);
    expect(result.current.stage).toBe('finalHold');
    expect(result.current.isActive).toBe(true);
    expect(result.current.isDone).toBe(false);

    // Completion marker at the nominal 10s boundary.
    act(() => {
      vi.advanceTimersByTime(OPENING_TOTAL_DURATION_MS - elapsed);
    });
    expect(result.current.isDone).toBe(true);
    expect(result.current.isActive).toBe(false);
    expect(result.current.stage).toBe('finalHold');
  });

  it('menjalankan tepat satu rantai timer (10 timeout) per mount', () => {
    renderHook(() => hook.useOpeningAnimation());
    // 9 stage transitions + 1 completion marker.
    expect(vi.getTimerCount()).toBe(10);
  });

  it('membersihkan SEMUA timer saat unmount (tidak ada setState setelah unmount)', () => {
    const { unmount } = renderHook(() => hook.useOpeningAnimation());
    expect(vi.getTimerCount()).toBe(10);

    unmount();
    expect(vi.getTimerCount()).toBe(0);

    // Advancing past the whole timeline after unmount schedules nothing new
    // and fires nothing — no setState-after-unmount possible.
    act(() => {
      vi.advanceTimersByTime(OPENING_TOTAL_DURATION_MS + 5000);
    });
    expect(vi.getTimerCount()).toBe(0);
  });

  it('React StrictMode (double-mount effect) tidak menggandakan timeline', () => {
    const { result } = renderHook(() => hook.useOpeningAnimation(), {
      wrapper: StrictWrapper,
    });

    // StrictMode runs setup -> cleanup -> setup; proper cleanup means exactly
    // one live chain remains (a leak would leave 20 pending timers).
    expect(vi.getTimerCount()).toBe(10);

    act(() => {
      vi.advanceTimersByTime(OPENING_TOTAL_DURATION_MS);
    });
    expect(result.current.stage).toBe('finalHold');
    expect(result.current.isDone).toBe(true);
  });

  it('safety fallback: ketika penjadwalan melempar error, langsung menuju final state', () => {
    vi.spyOn(window, 'setTimeout').mockImplementation(() => {
      throw new Error('scheduling broken');
    });

    const { result } = renderHook(() => hook.useOpeningAnimation());

    expect(result.current.stage).toBe('finalHold');
    expect(result.current.isDone).toBe(true);
    expect(result.current.isActive).toBe(false);
  });
});

describe('useOpeningAnimation — playback rules', () => {
  it('flag sudah tercatat (reload/revisit setelah login gagal) -> intro dilewati', () => {
    window.sessionStorage.setItem(OPENING_SESSION_STORAGE_KEY, '1');

    const { result } = renderHook(() => hook.useOpeningAnimation());

    expect(result.current.isActive).toBe(false);
    expect(result.current.isDone).toBe(true);
    expect(result.current.stage).toBe('finalHold');
    expect(vi.getTimerCount()).toBe(0);
  });

  it('prefers-reduced-motion -> melewati animasi panjang, Login langsung final, flag tetap tercatat', () => {
    vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({ matches: true }));

    const { result } = renderHook(() => hook.useOpeningAnimation());

    expect(result.current.isActive).toBe(false);
    expect(result.current.stage).toBe('finalHold');
    expect(result.current.isDone).toBe(true);
    expect(vi.getTimerCount()).toBe(0);
    // Playback status still recorded so the intro does not reappear
    // inconsistently later.
    expect(window.sessionStorage.getItem(OPENING_SESSION_STORAGE_KEY)).toBe('1');
  });

  it('sessionStorage gagal total -> tidak ada exception dan intro tetap berjalan', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('storage blocked');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('storage blocked');
    });

    let active = false;
    let stage = '';
    expect(() => {
      const { result } = renderHook(() => hook.useOpeningAnimation());
      active = result.current.isActive;
      stage = result.current.stage;
    }).not.toThrow();

    expect(active).toBe(true);
    expect(stage).toBe('initial');
    expect(vi.getTimerCount()).toBe(10);
  });
});
