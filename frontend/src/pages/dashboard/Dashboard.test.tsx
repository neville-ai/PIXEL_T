import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { listHistory, type HistoryList } from '@/utils/analysis';
import { Dashboard } from './index';

vi.mock('@/utils/analysis', () => ({
  listHistory: vi.fn(),
}));

const mockedListHistory = vi.mocked(listHistory);

function makeLatestItem(): HistoryList {
  return {
    items: [
      {
        id: 'analysis-9',
        created_at: '2026-10-06T14:15:00Z',
        completed_at: '2026-10-06T14:16:00Z',
        status: 'completed',
        original_filename: 'SCOPE_LATEST.png',
        thumbnail_url: null,
        segmentation_status: 'detected',
      },
    ],
  };
}

function renderDashboard() {
  return render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <Routes>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analysis/new" element={<div>NEW ANALYSIS PAGE</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  mockedListHistory.mockReset();
});

afterEach(() => {
  cleanup();
});

/**
 * P-06 — Elemen interaktif bersarang (regresi).
 *
 * CTA EmptyState "Mulai Analisis Baru" sebelumnya dirender sebagai
 * `<Link to><Button>…</Button></Link>` (anchor membungkus tombol); kini tombol
 * biasa dengan `navigate()` (pola A11Y-03). CTA hero bergaya tombol dan link
 * teks "Lihat Hasil"/"See All" TIDAK bersarang dan dijaga tetap link sungguhan
 * (guard href hero juga dipin oleh App.test).
 */
describe('Dashboard — CTA dan aksi tanpa elemen interaktif bersarang (P-06)', () => {
  it('CTA EmptyState "Start New Analysis" is a button navigating to /analysis/new', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    const { container } = renderDashboard();

    const cta = await screen.findByRole('button', { name: 'Start New Analysis' });
    expect(container.querySelector('a button, button a, a a, button button')).toBeNull();

    fireEvent.click(cta);
    expect(await screen.findByText('NEW ANALYSIS PAGE')).toBeTruthy();
  });

  it('CTA hero remains a styled link with href /analysis/new', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    renderDashboard();

    await screen.findByRole('heading', { name: 'Start New Analysis' });
    const cta = screen.getByRole('link', { name: /New Analysis/ });
    expect(cta.getAttribute('href')).toBe('/analysis/new');
    // Decorative Plus icon does not add noise to accessible name.
    expect(cta.querySelector('svg')?.getAttribute('aria-hidden')).toBe('true');
  });

  it('latest card action remains a plain text link without nested button', async () => {
    mockedListHistory.mockResolvedValue(makeLatestItem());
    const { container } = renderDashboard();

    expect(await screen.findByText('SCOPE_LATEST.png')).toBeTruthy();
    const link = screen.getByRole('link', { name: /View Result/ });
    expect(link.getAttribute('href')).toBe('/analysis/analysis-9');
    expect(container.querySelector('a button, button a')).toBeNull();
  });
});
