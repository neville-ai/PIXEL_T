import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { supabase } from '@/lib/supabase';
import { deleteAnalysis, listHistory } from './analysis';

vi.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: vi.fn(),
    },
  },
  isSupabaseConfigured: true,
}));

const mockedGetSession = vi.mocked(supabase.auth.getSession);

function session_ok() {
  mockedGetSession.mockResolvedValue({
    data: { session: { access_token: 'test-token' } },
    error: null,
  } as never);
}

function jsonResponse(body: unknown, ok = true) {
  return {
    ok,
    json: async () => body,
  } as Response;
}

beforeEach(() => {
  mockedGetSession.mockReset();
  session_ok();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('analysis service history methods', () => {
  it('listHistory calls GET /history with the bearer token', async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse({ success: true, data: { items: [] } }),
    );
    vi.stubGlobal('fetch', fetchMock);

    const result = await listHistory();

    expect(result).toEqual({ items: [] });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls).toHaveLength(1);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit & { headers: Record<string, string> }];
    expect(url).toContain('/history');
    expect(init.method).toBe('GET');
    expect(init.headers.Authorization).toBe('Bearer test-token');
  });

  it('deleteAnalysis calls DELETE /history/<id> and accepts a dataless success body', async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse({ success: true, message: 'Analysis deleted successfully' }),
    );
    vi.stubGlobal('fetch', fetchMock);

    await deleteAnalysis('analysis-9');

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls).toHaveLength(1);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit & { headers: Record<string, string> }];
    expect(url.endsWith('/history/analysis-9')).toBe(true);
    expect(init.method).toBe('DELETE');
    expect(init.headers.Authorization).toBe('Bearer test-token');
  });

  it('deleteAnalysis surfaces the server error message on failure', async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse(
        { success: false, error: { code: 'ANALYSIS_NOT_FOUND', message: 'Tidak ditemukan.' } },
        false,
      ),
    );
    vi.stubGlobal('fetch', fetchMock);

    await expect(deleteAnalysis('missing')).rejects.toThrow('Tidak ditemukan.');
  });
});
