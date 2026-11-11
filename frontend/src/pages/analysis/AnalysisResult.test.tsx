import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { getAnalysis, type AnalysisDetail } from '@/utils/analysis';
import { AnalysisResult } from './AnalysisResult';

vi.mock('@/utils/analysis', () => ({
  getAnalysis: vi.fn(),
}));

const mockedGetAnalysis = vi.mocked(getAnalysis);

function makeAnalysis(status: AnalysisDetail['analysis']['status']): AnalysisDetail {
  return {
    analysis: {
      id: 'analysis-42',
      status,
      created_at: '2026-09-30T10:00:00Z',
      original_filename: 'scope.jpg',
      error_code: null,
      error_message: null,
    },
    input: {
      original_image_url: 'https://storage.example/signed/original.jpg',
      width: 640,
      height: 480,
      mime_type: 'image/jpeg',
    },
  };
}

function renderPage(path = '/analysis/analysis-42') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/analysis/:id" element={<AnalysisResult />} />
        <Route path="*" element={<AnalysisResult />} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  mockedGetAnalysis.mockReset();
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe('AnalysisResult', () => {
  it('shows loading state while the authenticated detail request is pending', () => {
    mockedGetAnalysis.mockReturnValue(new Promise<AnalysisDetail>(() => {}));
    renderPage();

    expect(screen.getByRole('status').textContent).toContain('Memuat status analisis');
    expect(mockedGetAnalysis).toHaveBeenCalledWith('analysis-42');
  });

  it('renders processing status and the signed original image', async () => {
    mockedGetAnalysis.mockResolvedValue(makeAnalysis('processing'));
    renderPage();

    expect(await screen.findByText('Analysis is being processed.')).toBeTruthy();
    expect(screen.getByRole('img', { name: 'Original image: scope.jpg' }).getAttribute('src'))
      .toBe('https://storage.example/signed/original.jpg');
    expect(screen.getByText('640 × 480 px')).toBeTruthy();
  });

  it('renders completed state with unavailable output sections and no invented result', async () => {
    mockedGetAnalysis.mockResolvedValue(makeAnalysis('completed'));
    renderPage('/analysis/case-9');

    expect(await screen.findByRole('heading', { name: 'Analysis Result' })).toBeTruthy();
    expect(mockedGetAnalysis).toHaveBeenCalledWith('case-9');
    expect(screen.getByText('completed')).toBeTruthy();
    expect(screen.getAllByText('Segmentation output is not available yet.')).toHaveLength(2);
    expect(screen.getAllByText('Grad-CAM output is not available yet.')).toHaveLength(2);
    expect(screen.getByText('Model analysis is not available yet.')).toBeTruthy();
    expect(screen.getByText('Analysis summary is not available yet.')).toBeTruthy();
    expect(screen.queryByText(/confidence|dice|iou|malignancy/i)).toBeNull();
  });

  it('renders only completed assets and measurements supplied by the API', async () => {
    mockedGetAnalysis.mockResolvedValue({
      ...makeAnalysis('completed'),
      segmentation: {
        binary_mask_url: 'https://storage.example/signed/mask.png',
        overlay_url: null,
      },
      model_analysis: { area_pixels: 19 },
      summary: { text: 'Persisted summary.' },
    });
    renderPage();

    expect(await screen.findByRole('img', { name: 'Segmentation mask' })).toBeTruthy();
    expect(screen.getByText('19 px')).toBeTruthy();
    expect(screen.getByText('Persisted summary.')).toBeTruthy();
    expect(screen.getByText('Segmentation output is not available yet.')).toBeTruthy();
    expect(screen.queryByText(/confidence|dice|iou|malignancy/i)).toBeNull();
  });

  it('renders a safe failed state without exposing stored error details', async () => {
    mockedGetAnalysis.mockResolvedValue({
      ...makeAnalysis('failed'),
      analysis: {
        ...makeAnalysis('failed').analysis,
        error_code: 'ANALYSIS_FAILED',
        error_message: 'Analysis could not be completed. Please try again.',
      },
    });
    renderPage();

    expect(await screen.findByRole('alert')).toBeTruthy();
    expect(screen.getByText('Analysis could not be completed. Please try again.')).toBeTruthy();
    expect(screen.queryByText(/traceback|filesystem|private key/i)).toBeNull();
  });

  it('shows a request error and handles a missing route parameter', async () => {
    mockedGetAnalysis.mockRejectedValue(new Error('Analysis not found or access denied.'));
    renderPage();
    expect(await screen.findByRole('alert')).toBeTruthy();

    cleanup();
    renderPage('/');
    expect(screen.getByRole('alert').textContent).toContain('ID analisis tidak ditemukan');
    expect(mockedGetAnalysis).toHaveBeenCalledTimes(1);
  });

  it('polls processing status at a bounded interval and stops after completion', async () => {
    vi.useFakeTimers();
    mockedGetAnalysis
      .mockResolvedValueOnce(makeAnalysis('processing'))
      .mockResolvedValueOnce(makeAnalysis('completed'));
    renderPage();

    await act(async () => { await Promise.resolve(); });
    expect(screen.getByText('Analysis is being processed.')).toBeTruthy();

    await act(async () => { await vi.advanceTimersByTimeAsync(5000); });
    expect(screen.getByText('completed')).toBeTruthy();
    await act(async () => { await vi.advanceTimersByTimeAsync(60000); });
    expect(mockedGetAnalysis).toHaveBeenCalledTimes(2);
  });
});
