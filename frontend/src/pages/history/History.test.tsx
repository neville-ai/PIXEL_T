import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { deleteAnalysis, listHistory, type HistoryList } from '@/services/analysis';
import { History } from './History';

vi.mock('@/services/analysis', () => ({
  listHistory: vi.fn(),
  deleteAnalysis: vi.fn(),
}));

const mockedListHistory = vi.mocked(listHistory);
const mockedDeleteAnalysis = vi.mocked(deleteAnalysis);

function makeList(): HistoryList {
  return {
    items: [
      {
        id: 'analysis-1',
        created_at: '2026-09-30T10:00:00Z',
        completed_at: '2026-09-30T10:01:00Z',
        status: 'completed',
        original_filename: 'scope-1.jpg',
        thumbnail_url: 'https://storage.example/signed/thumb-1.jpg',
        segmentation_status: 'detected',
      },
      {
        id: 'analysis-2',
        created_at: '2026-09-29T10:00:00Z',
        completed_at: null,
        status: 'completed',
        original_filename: 'scope-2.png',
        thumbnail_url: null,
        segmentation_status: 'not_detected',
      },
    ],
  };
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/history']}>
      <Routes>
        <Route path="/history" element={<History />} />
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

    expect(await screen.findByText('scope-1.jpg')).toBeTruthy();
    expect(screen.getByText('scope-2.png')).toBeTruthy();
    expect(mockedListHistory).toHaveBeenCalledTimes(1);
    expect(document.body.textContent).not.toContain('sample-hist-001');
    expect(document.body.textContent).not.toContain('sample-hist-002');
    expect(document.body.textContent).not.toContain('Sesi Pemeriksaan Contoh');
  });

  it('shows an empty state when no analyses exist', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    renderPage();

    expect(await screen.findByText('Belum ada riwayat pemeriksaan')).toBeTruthy();
  });

  it('shows an error state with retry when loading fails', async () => {
    mockedListHistory.mockRejectedValueOnce(new Error('Server sibuk.'));
    mockedListHistory.mockResolvedValueOnce({ items: [] });
    renderPage();

    expect(await screen.findByText('Server sibuk.')).toBeTruthy();
    fireEvent.click(screen.getByText('Coba Lagi'));
    expect(await screen.findByText('Belum ada riwayat pemeriksaan')).toBeTruthy();
    expect(mockedListHistory).toHaveBeenCalledTimes(2);
  });

  it('opens a confirmation dialog before deleting and refreshes the list after confirm', async () => {
    mockedListHistory.mockResolvedValue(makeList());
    mockedDeleteAnalysis.mockResolvedValue(undefined);
    renderPage();

    expect(await screen.findByText('scope-1.jpg')).toBeTruthy();
    fireEvent.click(screen.getAllByText('Hapus')[0]);

    expect(await screen.findByText('Hapus riwayat pemeriksaan?')).toBeTruthy();
    expect(mockedDeleteAnalysis).not.toHaveBeenCalled();

    fireEvent.click(screen.getByText('Ya, Hapus'));

    await waitFor(() => {
      expect(mockedDeleteAnalysis).toHaveBeenCalledWith('analysis-1');
    });
    await waitFor(() => {
      expect(screen.queryByText('scope-1.jpg')).toBeNull();
    });
    expect(screen.getByText('scope-2.png')).toBeTruthy();
  });

  it('keeps the item and shows a safe error when deletion fails', async () => {
    mockedListHistory.mockResolvedValue(makeList());
    mockedDeleteAnalysis.mockRejectedValue(new Error('Gagal menghapus.'));
    renderPage();

    expect(await screen.findByText('scope-1.jpg')).toBeTruthy();
    fireEvent.click(screen.getAllByText('Hapus')[0]);
    expect(await screen.findByText('Hapus riwayat pemeriksaan?')).toBeTruthy();
    fireEvent.click(screen.getByText('Ya, Hapus'));

    expect(await screen.findByText('Gagal menghapus.')).toBeTruthy();
    expect(screen.getAllByText('scope-1.jpg').length).toBeGreaterThan(0);
  });
});
