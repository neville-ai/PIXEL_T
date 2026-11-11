import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

type TimelineModule = typeof import('./openingTimeline');

/**
 * Each test loads a fresh copy of the module so module-level playback state
 * (in-memory fallback flag, last-unmount marker) never leaks between tests.
 */
let t: TimelineModule;

// Keep references to the original Storage methods so we can restore them
// explicitly. vi.unstubAllGlobals() does not reliably restore prototype
// spies in this project's Vitest configuration, so we do it by hand.
const _origStorageGetItem = Storage.prototype.getItem;
const _origStorageSetItem = Storage.prototype.setItem;
const _origStorageRemoveItem = Storage.prototype.removeItem;

beforeEach(async () => {
  vi.resetModules();
  window.sessionStorage.clear();
  window.localStorage.clear();
  // Restore prototype methods to guard against leakage from previous tests.
  Storage.prototype.getItem = _origStorageGetItem;
  Storage.prototype.setItem = _origStorageSetItem;
  Storage.prototype.removeItem = _origStorageRemoveItem;
  t = await import('./openingTimeline');
});

afterEach(() => {
  vi.unstubAllGlobals();
  // Extra safety net: re-restore prototype methods.
  Storage.prototype.getItem = _origStorageGetItem;
  Storage.prototype.setItem = _origStorageSetItem;
  Storage.prototype.removeItem = _origStorageRemoveItem;
});

describe('timeline constants — 10 stages, nominal 10 seconds', () => {
  it('memiliki tepat 10 tahap dengan urutan sesuai spesifikasi', () => {
    expect([...t.OPENING_STAGES]).toEqual([
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
    ]);
    expect(t.OPENING_STAGES).toHaveLength(10);
  });

  it('start time tahap pertama 0 dan naik secara ketat', () => {
    const starts = t.OPENING_STAGES.map((s) => t.OPENING_STAGE_START_MS[s]);
    expect(starts[0]).toBe(0);
    for (let i = 1; i < starts.length; i += 1) {
      expect(starts[i]).toBeGreaterThan(starts[i - 1]);
    }
  });

  it('total durasi nominal tepat 10.000 ms dan finalHold mulai di 9.000 ms', () => {
    expect(t.OPENING_TOTAL_DURATION_MS).toBe(10000);
    expect(t.OPENING_STAGE_START_MS.finalHold).toBe(9000);
  });

  it('durasi per tahap sama dengan spesifikasi dan menjumlah 10.000 ms', () => {
    const starts = t.OPENING_STAGES.map((s) => t.OPENING_STAGE_START_MS[s]);
    const durations = starts.map((start, i) =>
      i + 1 < starts.length ? starts[i + 1] - start : t.OPENING_TOTAL_DURATION_MS - start
    );
    expect(durations).toEqual([700, 900, 900, 800, 700, 2000, 1000, 1200, 800, 1000]);
    const sum = durations.reduce((acc, d) => acc + d, 0);
    expect(sum).toBe(t.OPENING_TOTAL_DURATION_MS);
  });
});

describe('stageAtElapsed — deterministik, tanpa lompatan', () => {
  it('memetakan batas bawah setiap tahap dengan benar', () => {
    expect(t.stageAtElapsed(0)).toBe('initial');
    expect(t.stageAtElapsed(699)).toBe('initial');
    expect(t.stageAtElapsed(700)).toBe('focalPixelFormation');
    expect(t.stageAtElapsed(1599)).toBe('focalPixelFormation');
    expect(t.stageAtElapsed(1600)).toBe('supportingPixels');
    expect(t.stageAtElapsed(2499)).toBe('supportingPixels');
    expect(t.stageAtElapsed(2500)).toBe('segmentationFrame');
    expect(t.stageAtElapsed(3300)).toBe('completeLogo');
    expect(t.stageAtElapsed(4000)).toBe('identityMoment');
    expect(t.stageAtElapsed(5999)).toBe('identityMoment');
    expect(t.stageAtElapsed(6000)).toBe('logoTransition');
    expect(t.stageAtElapsed(7000)).toBe('loginUiReveal');
    expect(t.stageAtElapsed(8200)).toBe('layoutSettlement');
    expect(t.stageAtElapsed(9000)).toBe('finalHold');
    expect(t.stageAtElapsed(9999)).toBe('finalHold');
    expect(t.stageAtElapsed(t.OPENING_TOTAL_DURATION_MS)).toBe('finalHold');
    expect(t.stageAtElapsed(t.OPENING_TOTAL_DURATION_MS + 5000)).toBe('finalHold');
  });

  it('nilai negatif di-clamp ke initial', () => {
    expect(t.stageAtElapsed(-500)).toBe('initial');
  });

  it('hanya bergerak majur — tahap tidak pernah melompat mundur atau terlewat', () => {
    let previous = -1;
    const seen = new Set<number>();
    for (let ms = 0; ms <= t.OPENING_TOTAL_DURATION_MS; ms += 50) {
      const index = t.stageIndex(t.stageAtElapsed(ms));
      expect(index).toBeGreaterThanOrEqual(previous);
      previous = index;
      seen.add(index);
    }
    // Full coverage: every stage index observed across the sweep.
    expect(seen.size).toBe(10);
  });

  it('setiap tahap dapat dicapai tepat pada start time-nya', () => {
    const reached = new Set(
      t.OPENING_STAGES.map((s) => t.stageAtElapsed(t.OPENING_STAGE_START_MS[s]))
    );
    expect(reached.size).toBe(10);
  });
});

describe('session flag — playback rules', () => {
  it('sesi baru: intro dianggap belum pernah diputar', () => {
    expect(t.hasOpeningPlayed()).toBe(false);
    expect(t.shouldPlayIntro()).toBe(true);
  });

  it('setelah flag tercatat, intro tidak diputar lagi (termasuk setelah login gagal)', () => {
    t.markOpeningPlayed();
    expect(t.hasOpeningPlayed()).toBe(true);
    expect(window.sessionStorage.getItem(t.OPENING_SESSION_STORAGE_KEY)).toBe('1');
    expect(t.shouldPlayIntro()).toBe(false);
  });

  it('remount segera (cycle dev StrictMode) tetap memutar; revisit sesungguhnya melewati', () => {
    t.markOpeningPlayed();
    t.noteOpeningUnmount(1_000_000);
    // Immediate remount inside the strict-remount window -> play (dev only).
    expect(t.shouldPlayIntro(1_000_100)).toBe(true);
    // A genuine later revisit (logout -> /login, dll.) -> skip.
    expect(t.shouldPlayIntro(1_001_000)).toBe(false);
  });

  it('kegagalan sessionStorage tidak merusak keputusan (fallback memori)', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('storage blocked');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('storage blocked');
    });

    // Fresh state with broken storage -> still decides to play, no throw.
    expect(t.shouldPlayIntro()).toBe(true);
    expect(() => t.markOpeningPlayed()).not.toThrow();
    // In-memory fallback prevents a replay for this page load.
    expect(t.hasOpeningPlayed()).toBe(true);
    expect(t.shouldPlayIntro()).toBe(false);
  });

  it('status intro disimpan di sessionStorage, BUKAN localStorage (isolasi per tab)', () => {
    t.markOpeningPlayed();
    expect(window.sessionStorage.getItem(t.OPENING_SESSION_STORAGE_KEY)).toBe('1');
    // Must never leak into localStorage — that would replay across tabs.
    expect(window.localStorage.getItem(t.OPENING_SESSION_STORAGE_KEY)).toBeNull();
  });

  it('tab baru (sessionStorage kosong) memutar intro lagi', () => {
    // Simulate a brand-new tab: no session flag, fresh module state.
    window.sessionStorage.clear();
    expect(t.hasOpeningPlayed()).toBe(false);
    expect(t.shouldPlayIntro()).toBe(true);
  });
});

describe('prefersReducedMotion', () => {
  it('mengembalikan false ketika matchMedia tidak tersedia', () => {
    vi.stubGlobal('matchMedia', undefined);
    expect(t.prefersReducedMotion()).toBe(false);
  });

  it('mengembalikan true ketika user meminta reduce motion', () => {
    vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({ matches: true }));
    expect(t.prefersReducedMotion()).toBe(true);
  });

  it('mengembalikan false pada kondisi normal (tanpa preferensi reduce)', () => {
    // jsdom: matchMedia ada dan tidak cocok dengan reduce.
    expect(t.prefersReducedMotion()).toBe(false);
  });
});

describe('remembered e-mail helper', () => {
  it('menyimpan e-mail saja dan dapat dibersihkan', () => {
    t.setRememberedEmail('dokter@rumah-sakit.id');
    expect(t.getRememberedEmail()).toBe('dokter@rumah-sakit.id');
    expect(window.localStorage.getItem(t.REMEMBERED_EMAIL_STORAGE_KEY)).toBe(
      'dokter@rumah-sakit.id'
    );
    // Never any password-like value in storage.
    const allStorage = JSON.stringify({
      local: window.localStorage,
      session: window.sessionStorage,
    });
    expect(allStorage).not.toContain('password');

    t.setRememberedEmail(null);
    expect(t.getRememberedEmail()).toBeNull();
  });

  it('localStorage yang gagal tidak melempar exception', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('storage blocked');
    });
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('storage blocked');
    });
    vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
      throw new Error('storage blocked');
    });

    expect(() => t.setRememberedEmail('a@b.com')).not.toThrow();
    expect(t.getRememberedEmail()).toBeNull();
  });
});
