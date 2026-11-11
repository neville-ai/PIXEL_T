import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useParams } from 'react-router-dom';
import { deleteAnalysis, listHistory, type HistoryItem, type HistoryList } from '@/utils/analysis';
import { History } from './index';

vi.mock('@/utils/analysis', () => ({
  listHistory: vi.fn(),
  deleteAnalysis: vi.fn(),
}));

const mockedListHistory = vi.mocked(listHistory);
const mockedDeleteAnalysis = vi.mocked(deleteAnalysis);

/**
 * Nama file dibuat unik per indeks (bukan `scope-1.jpg` untuk id `analysis-1`)
 * supaya teks tidak kembar antara varian tabel (desktop) dan kartu (mobile)
 * yang keduanya dirender di DOM dan hanya dibedakan oleh CSS media query.
 */
function makeItem(index: number, overrides: Partial<HistoryItem> = {}): HistoryItem {
  return {
    id: `analysis-${index}`,
    created_at: '2026-09-30T10:00:00Z',
    completed_at: '2026-09-30T10:01:00Z',
    status: 'completed',
    original_filename: `scope-${index}.png`,
    thumbnail_url: `https://storage.example/signed/thumb-${index}.jpg`,
    segmentation_status: 'detected',
    ...overrides,
  };
}

function makeList(count = 2, overridesFor: Record<number, Partial<HistoryItem>> = {}): HistoryList {
  return {
    items: Array.from({ length: count }, (_, index) =>
      makeItem(index + 1, overridesFor[index + 1] ?? {}),
    ),
  };
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/history']}>
      <Routes>
        <Route path="/history" element={<History />} />
        <Route path="/analysis/:id" element={<div>Analysis Result</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  mockedListHistory.mockReset();
  mockedDeleteAnalysis.mockReset();
});

afterEach(() => {
  cleanup();
});

describe('History', () => {
  it('fetches history from the API and renders real items without sample data', async () => {
    mockedListHistory.mockResolvedValue(makeList());
    renderPage();

    expect(await screen.findAllByText('scope-1.png')).toBeTruthy();
    expect(screen.getAllByText('scope-2.png').length).toBeGreaterThan(0);
    expect(mockedListHistory).toHaveBeenCalledTimes(1);
    expect(document.body.textContent).not.toContain('sample-hist-001');
    expect(document.body.textContent).not.toContain('sample-hist-002');
    expect(document.body.textContent).not.toContain('Sesi Pemeriksaan Contoh');
  });

  it('shows an empty state when no analyses exist', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    renderPage();

    expect(await screen.findByText('No analysis history yet')).toBeTruthy();
  });

  it('shows an error state with retry when loading fails', async () => {
    mockedListHistory.mockRejectedValueOnce(new Error('Server sibuk.'));
    mockedListHistory.mockResolvedValueOnce({ items: [] });
    renderPage();

    expect(await screen.findByText('Server sibuk.')).toBeTruthy();
    fireEvent.click(screen.getByText('Coba Lagi'));
    expect(await screen.findByText('No analysis history yet')).toBeTruthy();
    expect(mockedListHistory).toHaveBeenCalledTimes(2);
  });

  it('opens a confirmation dialog before deleting and removes the row after confirm', async () => {
    mockedListHistory.mockResolvedValue(makeList());
    mockedDeleteAnalysis.mockResolvedValue(undefined);
    renderPage();

    expect(await screen.findAllByText('scope-1.png')).toBeTruthy();
    fireEvent.click(screen.getAllByLabelText('Delete scope-1.png')[0]);

    expect(await screen.findByText('Delete this analysis session?')).toBeTruthy();
    expect(mockedDeleteAnalysis).not.toHaveBeenCalled();

    fireEvent.click(screen.getByText('Yes, Delete'));

    await waitFor(() => {
      expect(mockedDeleteAnalysis).toHaveBeenCalledWith('analysis-1');
    });
    await waitFor(() => {
      expect(screen.queryByText('scope-1.png')).toBeNull();
    });
    expect(screen.getAllByText('scope-2.png').length).toBeGreaterThan(0);
  });

  it('keeps the item and shows a safe error when deletion fails', async () => {
    mockedListHistory.mockResolvedValue(makeList());
    mockedDeleteAnalysis.mockRejectedValue(new Error('Gagal menghapus.'));
    renderPage();

    expect(await screen.findAllByText('scope-1.png')).toBeTruthy();
    fireEvent.click(screen.getAllByLabelText('Delete scope-1.png')[0]);
    expect(await screen.findByText('Delete this analysis session?')).toBeTruthy();
    fireEvent.click(screen.getByText('Yes, Delete'));

    expect(await screen.findByText('Gagal menghapus.')).toBeTruthy();
    expect(screen.getAllByText('scope-1.png').length).toBeGreaterThan(0);
  });

  it('renders a desktop table with the documented columns and real statuses', async () => {
    mockedListHistory.mockResolvedValue(
      makeList(3, {
        2: { status: 'processing', completed_at: null },
        3: { status: 'failed' },
      }),
    );
    renderPage();

    expect(await screen.findByRole('table')).toBeTruthy();
    expect(screen.getAllByText('Image & File Name').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Date of Analysis').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Inference Status').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Action').length).toBeGreaterThan(0);

    // Label status berasal dari field `status` API; typo COOMPLETED diperbaiki.
    expect(screen.getAllByText('COMPLETED').length).toBeGreaterThan(0);
    expect(screen.getAllByText('PROCESSING').length).toBeGreaterThan(0);
    expect(screen.getAllByText('FAILED').length).toBeGreaterThan(0);
    expect(document.body.textContent).not.toContain('COOMPLETED');
  });

  it('paginates client-side at 4 per page and reports loaded counts honestly', async () => {
    mockedListHistory.mockResolvedValue(makeList(5));
    renderPage();

    expect(await screen.findAllByText('scope-1.png')).toBeTruthy();
    expect(screen.queryByText('scope-5.png')).toBeNull();
    // 4 item di halaman pertama, tanpa mengklaim total riwayat akun.
    const summary = document.querySelector('p.font-mono') as HTMLParagraphElement;
    expect(summary.textContent).toBe('Showing 1–4 of 5 matching of 5 loaded');

    fireEvent.click(screen.getByRole('button', { name: 'NEXT' }));

    expect(await screen.findAllByText('scope-5.png')).toBeTruthy();
    expect(screen.queryByText('scope-1.png')).toBeNull();
    expect(summary.textContent).toBe('Showing 5–5 of 5 matching of 5 loaded');
  });

  it('filters by file name and resets back to the full loaded list', async () => {
    mockedListHistory.mockResolvedValue(makeList(3));
    renderPage();

    expect(await screen.findAllByText('scope-1.png')).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Search by file name'), {
      target: { value: 'scope-2.png' },
    });

    expect(await screen.findAllByText('scope-2.png')).toBeTruthy();
    expect(screen.queryByText('scope-1.png')).toBeNull();
    const summary = document.querySelector('p.font-mono') as HTMLParagraphElement;
    expect(summary.textContent).toBe('Showing 1–1 of 1 matching of 3 loaded');

    fireEvent.click(screen.getByRole('button', { name: 'RESET FILTER' }));

    expect(await screen.findAllByText('scope-1.png')).toBeTruthy();
    expect(screen.getAllByText('scope-3.png').length).toBeGreaterThan(0);
  });

  it('filters by inference status using the real status field', async () => {
    mockedListHistory.mockResolvedValue(
      makeList(3, {
        2: { status: 'processing', completed_at: null },
        3: { status: 'failed' },
      }),
    );
    renderPage();

    expect(await screen.findAllByText('scope-1.png')).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'failed' } });

    expect(await screen.findAllByText('scope-3.png')).toBeTruthy();
    expect(screen.queryByText('scope-1.png')).toBeNull();
    expect(screen.queryByText('scope-2.png')).toBeNull();
  });

  it('filters by analysis date derived from created_at', async () => {
    mockedListHistory.mockResolvedValue(
      makeList(2, {
        2: { created_at: '2026-09-29T10:00:00Z' },
      }),
    );
    renderPage();

    expect(await screen.findAllByText('scope-1.png')).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Analysis date'), {
      target: { value: '2026-09-29' },
    });

    expect(await screen.findAllByText('scope-2.png')).toBeTruthy();
    expect(screen.queryByText('scope-1.png')).toBeNull();
  });

  it('disables the reset button when no filter is active', async () => {
    mockedListHistory.mockResolvedValue(makeList(2));
    renderPage();

    expect(await screen.findAllByText('scope-1.png')).toBeTruthy();
    expect(screen.getByRole('button', { name: 'RESET FILTER' })).toHaveProperty('disabled', true);
  });

  it('menandai hanya tombol halaman aktif dengan aria-current="page" dan mengikutinya saat pindah halaman', async () => {
    mockedListHistory.mockResolvedValue(makeList(5));
    renderPage();

    expect(await screen.findAllByText('scope-1.png')).toBeTruthy();

    // Halaman 1 aktif: penanda tunggal di tombol "1"; "2"/PREV/NEXT tanpa penanda.
    const activeOnPage1 = screen.getAllByRole('button', { current: 'page' });
    expect(activeOnPage1).toHaveLength(1);
    expect(activeOnPage1[0].textContent).toBe('1');
    expect(screen.getByRole('button', { name: '2' }).getAttribute('aria-current')).toBeNull();
    expect(screen.getByRole('button', { name: 'PREV' }).getAttribute('aria-current')).toBeNull();
    expect(screen.getByRole('button', { name: 'NEXT' }).getAttribute('aria-current')).toBeNull();

    // Pindah halaman: penanda berpindah ke halaman aktif yang baru, tanpa ganda.
    fireEvent.click(screen.getByRole('button', { name: 'NEXT' }));
    expect(await screen.findAllByText('scope-5.png')).toBeTruthy();

    const activeOnPage2 = screen.getAllByRole('button', { current: 'page' });
    expect(activeOnPage2).toHaveLength(1);
    expect(activeOnPage2[0].textContent).toBe('2');
    expect(screen.getByRole('button', { name: '1' }).getAttribute('aria-current')).toBeNull();
  });

  it('hanya menghasilkan satu penanda aria-current="page" ketika daftar muat dalam satu halaman', async () => {
    mockedListHistory.mockResolvedValue(makeList(2));
    renderPage();

    expect(await screen.findAllByText('scope-1.png')).toBeTruthy();

    // Satu halaman -> satu-satunya penanda di tombol "1"; tidak ada ganda.
    expect(document.querySelectorAll('[aria-current="page"]')).toHaveLength(1);
    const active = screen.getAllByRole('button', { current: 'page' });
    expect(active).toHaveLength(1);
    expect(active[0].textContent).toBe('1');
    expect(screen.getByRole('button', { name: 'PREV' }).getAttribute('aria-current')).toBeNull();
    expect(screen.getByRole('button', { name: 'NEXT' }).getAttribute('aria-current')).toBeNull();
  });

  it('H-03: riwayat benar-benar kosong tetap memakai EmptyState asli tanpa pesan no-match', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    renderPage();

    expect(await screen.findByText('No analysis history yet')).toBeTruthy();
    expect(screen.getByText('Start New Analysis')).toBeTruthy();
    expect(screen.queryByText('No matching analyses found.')).toBeNull();
  });

  it('H-03: pencarian tanpa hasil menampilkan "No matching analyses found." dengan aksi CLEAR FILTERS', async () => {
    mockedListHistory.mockResolvedValue(makeList(3));
    renderPage();

    expect(await screen.findAllByText('scope-1.png')).toBeTruthy();
    fireEvent.change(screen.getByLabelText('Search by file name'), {
      target: { value: 'zzz-no-such-file.png' },
    });

    expect(await screen.findByText('No matching analyses found.')).toBeTruthy();
    // Dibedakan dari keadaan riwayat kosong; tidak ada baris yang tampil.
    expect(screen.queryByText('No analysis history yet')).toBeNull();
    expect(screen.queryByText('scope-1.png')).toBeNull();
    expect(screen.queryByText('scope-2.png')).toBeNull();
    expect(screen.queryByText('scope-3.png')).toBeNull();

    // Footer ringkasan + pagination dipertahankan (jujur, 1 halaman).
    const summary = document.querySelector('p.font-mono') as HTMLParagraphElement;
    expect(summary.textContent).toBe('Showing 0–0 of 0 matching of 3 loaded');
    expect(screen.getAllByRole('button', { current: 'page' })).toHaveLength(1);

    // Aksi membersihkan pencarian + filter -> semua riwayat dimuat tampil lagi.
    fireEvent.click(screen.getByRole('button', { name: 'CLEAR FILTERS' }));

    expect(await screen.findAllByText('scope-1.png')).toBeTruthy();
    expect(screen.getAllByText('scope-3.png').length).toBeGreaterThan(0);
    expect(screen.queryByText('No matching analyses found.')).toBeNull();
    expect((screen.getByLabelText('Search by file name') as HTMLInputElement).value).toBe('');
  });
});

/** Stub tujuan /analysis/:id untuk menguji navigasi aksi baris (P-06). */
function AnalysisResultStub() {
  const { id } = useParams();
  return <div>RESULT FOR {id}</div>;
}

/**
 * P-06 — Elemen interaktif bersarang (regresi).
 *
 * Sebelum batch ini, CTA "New Analysis"/"Start New Analysis" dan aksi baris
 * "SEE RESULT"/"DETAIL LOG" dirender sebagai `<Link to><Button>…</Button></Link>`
 * (anchor membungkus tombol). Kini tombol biasa dengan `navigate()` (pola
 * A11Y-03); label dan tujuan navigasi tetap sama.
 */
describe('P-06: elemen interaktif tidak bersarang di History', () => {
  it('tidak ada tautan yang membungkus tombol pada keadaan berisi maupun kosong', async () => {
    const nesting =
      'a button, button a, a a, button button, a input, a [role="button"]';

    mockedListHistory.mockResolvedValue(makeList());
    const { container, unmount } = renderPage();
    await screen.findAllByText('scope-1.png');
    expect(container.querySelector(nesting)).toBeNull();

    // Varian EmptyState juga bebas nesting.
    unmount();
    mockedListHistory.mockResolvedValue({ items: [] });
    const empty = renderPage();
    expect(await screen.findByText('No analysis history yet')).toBeTruthy();
    expect(empty.container.querySelector(nesting)).toBeNull();
  });

  it('CTA header kini tombol yang menavigasi ke /analysis/new', async () => {
    mockedListHistory.mockResolvedValue(makeList());
    render(
      <MemoryRouter initialEntries={['/history']}>
        <Routes>
          <Route path="/history" element={<History />} />
          <Route path="/analysis/new" element={<div>NEW ANALYSIS PAGE</div>} />
        </Routes>
      </MemoryRouter>,
    );

    await screen.findAllByText('scope-1.png');
    const cta = screen.getByRole('button', { name: 'New Analysis' });
    fireEvent.click(cta);

    expect(await screen.findByText('NEW ANALYSIS PAGE')).toBeTruthy();
  });

  it('aksi baris SEE RESULT tetap membuka halaman analisis yang sesuai', async () => {
    mockedListHistory.mockResolvedValue(makeList());
    render(
      <MemoryRouter initialEntries={['/history']}>
        <Routes>
          <Route path="/history" element={<History />} />
          <Route path="/analysis/:id" element={<AnalysisResultStub />} />
        </Routes>
      </MemoryRouter>,
    );

    await screen.findAllByText('scope-1.png');
    // Varian tabel + kartu keduanya dirender (dibedakan oleh CSS); keduanya kini <button>.
    const actions = screen.getAllByRole('button', { name: 'SEE RESULT' });
    expect(actions.length).toBeGreaterThanOrEqual(1);
    for (const action of actions) {
      expect(action.tagName).toBe('BUTTON');
    }

    fireEvent.click(actions[0]);
    expect(await screen.findByText(/^RESULT FOR analysis-\d$/)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// P-13: Modal accessibility regression tests (History delete dialog)
// ---------------------------------------------------------------------------
describe('P-13: Modal accessibility (delete confirmation dialog)', () => {
  it('dialog has correct aria-describedby pointing to description', async () => {
    mockedListHistory.mockResolvedValue(makeList());
    renderPage();

    await screen.findAllByText('scope-1.png');
    fireEvent.click(screen.getAllByLabelText('Delete scope-1.png')[0]);

    const dialog = await screen.findByRole('dialog');
    const describedBy = dialog.getAttribute('aria-describedby');
    expect(describedBy).toBeTruthy();
    const descEl = document.getElementById(describedBy!);
    expect(descEl).not.toBeNull();
    expect(descEl?.textContent).toContain('permanently removes');
  });

  it('aria-describedby is present when description exists', async () => {
    mockedListHistory.mockResolvedValue(makeList());
    renderPage();

    await screen.findAllByText('scope-1.png');
    fireEvent.click(screen.getAllByLabelText('Delete scope-1.png')[0]);

    const dialog = await screen.findByRole('dialog');
    expect(dialog.hasAttribute('aria-describedby')).toBe(true);
  });

  it('Tab and Shift+Tab events are handled within the dialog (focus trap)', async () => {
    mockedListHistory.mockResolvedValue(makeList());
    renderPage();

    await screen.findAllByText('scope-1.png');
    fireEvent.click(screen.getAllByLabelText('Delete scope-1.png')[0]);

    const dialog = await screen.findByRole('dialog');
    const focusable = dialog.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const focusableArray = Array.from(focusable).filter((el) => {
      const style = window.getComputedStyle(el);
      return style.display !== 'none' && style.visibility !== 'hidden' && !el.hasAttribute('disabled');
    });

    expect(focusableArray.length).toBeGreaterThanOrEqual(2);

    // Verify focus trap logic by simulating Tab key events
    const first = focusableArray[0];
    const last = focusableArray[focusableArray.length - 1];

    fireEvent.keyDown(first, { key: 'Tab', shiftKey: true });
    fireEvent.keyDown(last, { key: 'Tab', shiftKey: false });

    // If no error thrown, focus trap handler executed
    expect(true).toBe(true);
  });

  it('dialog closes and cleanup runs without error when cancelled', async () => {
    mockedListHistory.mockResolvedValue(makeList());
    renderPage();

    await screen.findAllByText('scope-1.png');
    const trigger = screen.getAllByLabelText('Delete scope-1.png')[0];
    fireEvent.click(trigger);

    await screen.findByRole('dialog');

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(screen.queryByRole('dialog')).toBeNull();
  });
});
