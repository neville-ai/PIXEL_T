import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import {
  createAnalysis,
  getAnalysis,
  type AnalysisDetail,
  type CreatedAnalysis,
} from '@/services/analysis';
import { NewAnalysis } from './NewAnalysis';

vi.mock('@/services/analysis', () => ({
  createAnalysis: vi.fn(),
  getAnalysis: vi.fn(),
}));

const mockedCreateAnalysis = vi.mocked(createAnalysis);
const mockedGetAnalysis = vi.mocked(getAnalysis);

/** Bentuk minimal GET /api/analysis/{id} untuk polling progres halaman ini. */
function makeDetail(
  status: AnalysisDetail['analysis']['status'],
  progress?: { current_step?: string; progress_percent?: number },
): AnalysisDetail {
  return {
    analysis: {
      id: 'analysis-77',
      status,
      created_at: '2026-09-30T10:00:00Z',
      completed_at: null,
      original_filename: 'colonoscopy_frame_001.png',
      ...(progress ?? {}),
    },
    input: {
      original_image_url: null,
      width: 512,
      height: 512,
      mime_type: 'image/png',
    },
  };
}

/**
 * jsdom tidak mengimplementasikan `URL.createObjectURL` maupun
 * `createImageBitmap`, keduanya dipakai NewAnalysis untuk pratinjau dan
 * pemeriksaan dekoding citra.
 */
beforeEach(() => {
  mockedCreateAnalysis.mockReset();
  mockedGetAnalysis.mockReset();

  vi.stubGlobal(
    'createImageBitmap',
    vi.fn().mockResolvedValue({ width: 512, height: 512, close: vi.fn() }),
  );

  Object.defineProperty(URL, 'createObjectURL', {
    configurable: true,
    writable: true,
    value: vi.fn(() => 'blob:pixel-t-preview'),
  });
  Object.defineProperty(URL, 'revokeObjectURL', {
    configurable: true,
    writable: true,
    value: vi.fn(),
  });
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

function makeFile(
  name = 'colonoscopy_frame_001.png',
  type = 'image/png',
  size = 256 * 1024,
): File {
  const file = new File(['placeholder-bytes'], name, { type });
  Object.defineProperty(file, 'size', { value: size, configurable: true });
  return file;
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/analysis/new']}>
      <Routes>
        <Route path="/analysis/new" element={<NewAnalysis />} />
        <Route path="/analysis/:id" element={<div>Analysis Result Page</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

/** Input berkas tersembunyi yang dibuka oleh tombol browse. */
function fileInput(): HTMLInputElement {
  return screen.getByLabelText('Select endoscopy image file') as HTMLInputElement;
}

/**
 * Tombol submit diambil lewat atributnya, bukan lewat teks, karena labelnya
 * berubah mengikuti state (`Start analysis` / `Validating image...` /
 * `Uploading image...`).
 */
function submitButton(): HTMLButtonElement {
  return document.querySelector('button[type="submit"]') as HTMLButtonElement;
}

function selectViaInput(file: File): void {
  fireEvent.change(fileInput(), { target: { files: [file] } });
}

describe('NewAnalysis — header, breadcrumb, panel spesifikasi, dan tiga langkah', () => {
  it('menampilkan breadcrumb dua segmen, judul, dan subtitle referensi', () => {
    renderPage();

    expect(screen.getByRole('navigation', { name: 'Breadcrumb' })).toBeTruthy();

    const backLink = screen.getByRole('link', { name: /back to dashboard/i });
    expect(backLink.getAttribute('href')).toBe('/dashboard');

    expect(screen.getByRole('heading', { level: 1, name: /new analysis/i })).toBeTruthy();
    expect(screen.getByText(/upload a single colonoscopy image/i)).toBeTruthy();
  });

  it('menampilkan panel pipeline specification dengan nilai yang dapat diverifikasi', () => {
    renderPage();

    const panel = within(screen.getByTestId('pipeline-spec'));
    expect(panel.getByText(/pipeline specification/i)).toBeTruthy();

    // Tiga baris spesifikasi — semuanya memang diimplementasikan oleh
    // konstanta validasi pada halaman ini.
    expect(panel.getByText('Inference model')).toBeTruthy();
    expect(panel.getByText('U-Net + ResNet50')).toBeTruthy();
    expect(panel.getByText('Input format')).toBeTruthy();
    expect(panel.getByText('JPG, JPEG, PNG')).toBeTruthy();
    expect(panel.getByText('Max file size')).toBeTruthy();
    expect(panel.getByText('10 MB')).toBeTruthy();
  });

  it('menampilkan section What happens next? dengan tepat tiga langkah', () => {
    renderPage();

    const steps = within(screen.getByTestId('next-steps'));
    expect(steps.getByRole('heading', { level: 2, name: /what happens next/i })).toBeTruthy();
    expect(steps.getByText(/clinical workflow guidelines/i)).toBeTruthy();

    expect(steps.getAllByRole('heading', { level: 3 })).toHaveLength(3);
    expect(steps.getByRole('heading', { level: 3, name: /image format validation/i })).toBeTruthy();
    expect(
      steps.getByRole('heading', { level: 3, name: /u-net segmentation & grad-cam/i }),
    ).toBeTruthy();
    expect(
      steps.getByRole('heading', { level: 3, name: /results & saved sessions/i }),
    ).toBeTruthy();
  });

  it('tidak menjanjikan IoU/Dice per citra, verifikasi klinisi, cetak, atau ekspor', () => {
    const { container } = renderPage();

    const text = container.textContent ?? '';
    expect(text).not.toMatch(/iou/i);
    expect(text).not.toMatch(/dice/i);
    expect(text).not.toMatch(/clinician verification/i);
    expect(text).not.toMatch(/print/i);
    expect(text).not.toMatch(/export/i);
    expect(text).not.toMatch(/conv4/i);
  });
});

describe('NewAnalysis — status awal dan tombol nonaktif', () => {
  it('status awal sesuai referensi dan START ANALYSIS nonaktif tanpa berkas', () => {
    renderPage();

    expect(screen.getByText(/awaiting colonoscopy image files/i)).toBeTruthy();
    expect(
      screen.getByText(/select an image file first to begin inference/i),
    ).toBeTruthy();
    expect(submitButton().disabled).toBe(true);
  });

  it('tombol tetap nonaktif selama validasi berkas berlangsung', async () => {
    vi.stubGlobal('createImageBitmap', vi.fn(() => new Promise(() => {})));
    renderPage();

    selectViaInput(makeFile());

    await waitFor(() => {
      expect(submitButton().disabled).toBe(true);
    });
    expect(screen.getByText(/validating selected image file/i)).toBeTruthy();
    expect(screen.getByText(/checking format, size, and image dimensions/i)).toBeTruthy();
    expect(screen.getByRole('button', { name: /validating image/i })).toBeTruthy();
  });
});

describe('NewAnalysis — pemilihan berkas', () => {
  it('memilih berkas lewat input menampilkan preview dan mengaktifkan tombol', async () => {
    renderPage();

    selectViaInput(makeFile());

    expect(await screen.findByText('colonoscopy_frame_001.png')).toBeTruthy();
    expect(screen.getByAltText('Preview colonoscopy_frame_001.png')).toBeTruthy();
    expect(screen.getByText('256.0 KB · image/png')).toBeTruthy();
    expect(submitButton().disabled).toBe(false);
    expect(screen.getByText(/image file ready for inference/i)).toBeTruthy();
    expect(screen.getByText(/ready to begin inference/i)).toBeTruthy();
  });

  it('drag and drop memilih berkas langsung ke area unggah', async () => {
    renderPage();

    fireEvent.drop(screen.getByTestId('drop-zone'), {
      dataTransfer: { files: [makeFile('dropped_scan.png')] },
    });

    expect(await screen.findByText('dropped_scan.png')).toBeTruthy();
    expect(submitButton().disabled).toBe(false);
    expect(screen.getByText(/image file ready for inference/i)).toBeTruthy();
  });
});

describe('NewAnalysis — validasi berkas', () => {
  it('menolak format selain JPEG/PNG dan tetap menonaktifkan tombol', async () => {
    renderPage();

    selectViaInput(makeFile('scan.webp', 'image/webp'));

    expect(await screen.findByText('Select a JPG, JPEG, or PNG image.')).toBeTruthy();
    expect(screen.queryByText('colonoscopy_frame_001.png')).toBeNull();
    expect(submitButton().disabled).toBe(true);
    expect(screen.getByText(/awaiting colonoscopy image files/i)).toBeTruthy();
  });

  it('menolak berkas yang melebihi batas 10 MB (sesuai panel spesifikasi)', async () => {
    renderPage();

    selectViaInput(makeFile('huge_scan.png', 'image/png', 11 * 1024 * 1024));

    expect(await screen.findByText('File size exceeds the 10 MB limit.')).toBeTruthy();
    expect(submitButton().disabled).toBe(true);
  });

  it('menolak berkas citra kosong', async () => {
    renderPage();

    selectViaInput(makeFile('empty_scan.png', 'image/png', 0));

    expect(await screen.findByText('The image file is empty. Choose another file.')).toBeTruthy();
    expect(submitButton().disabled).toBe(true);
  });

  it('menolak berkas yang tidak dapat didekode sebagai citra', async () => {
    vi.stubGlobal(
      'createImageBitmap',
      vi.fn().mockRejectedValue(new Error('decode failed')),
    );
    renderPage();

    selectViaInput(makeFile());

    expect(
      await screen.findByText('This file cannot be read as a JPG, JPEG, or PNG image.'),
    ).toBeTruthy();
    expect(submitButton().disabled).toBe(true);
  });

  it('menerima berkas .jpeg dengan MIME type image/jpeg', async () => {
    renderPage();

    selectViaInput(makeFile('scan_frame.jpeg', 'image/jpeg'));

    expect(await screen.findByText('scan_frame.jpeg')).toBeTruthy();
    expect(screen.getByText('256.0 KB · image/jpeg')).toBeTruthy();
    expect(submitButton().disabled).toBe(false);
    expect(screen.getByText(/image file ready for inference/i)).toBeTruthy();
  });

  it('menerima berkas .jpg tanpa MIME type melalui ekstensinya', async () => {
    renderPage();

    selectViaInput(makeFile('scan_frame.jpg', ''));

    expect(await screen.findByText('scan_frame.jpg')).toBeTruthy();
    expect(submitButton().disabled).toBe(false);
    expect(screen.getByText(/image file ready for inference/i)).toBeTruthy();
  });

  it('menolak berkas yang ekstensi dan MIME type-nya tidak konsisten', async () => {
    renderPage();

    selectViaInput(makeFile('mask_label.png', 'image/jpeg'));

    expect(
      await screen.findByText(
        'The file extension and image type do not match. Choose a JPG, JPEG, or PNG file.',
      ),
    ).toBeTruthy();
    expect(submitButton().disabled).toBe(true);
    expect(screen.getByText(/awaiting colonoscopy image files/i)).toBeTruthy();
  });
});

describe('NewAnalysis — preview dan penghapusan berkas', () => {
  it('menghapus berkas terpilih mengembalikan halaman ke status awal', async () => {
    renderPage();

    selectViaInput(makeFile());
    await screen.findByText('colonoscopy_frame_001.png');

    fireEvent.click(screen.getByRole('button', { name: 'Remove selected image' }));

    await waitFor(() => {
      expect(screen.queryByText('colonoscopy_frame_001.png')).toBeNull();
    });
    expect(screen.queryByAltText('Preview colonoscopy_frame_001.png')).toBeNull();
    expect(submitButton().disabled).toBe(true);
    expect(screen.getByText(/awaiting colonoscopy image files/i)).toBeTruthy();
  });
});

describe('NewAnalysis — loading, kegagalan API, dan navigasi', () => {
  it('status loading aktif dan tombol nonaktif selama upload berlangsung', async () => {
    mockedCreateAnalysis.mockReturnValue(
      new Promise<CreatedAnalysis>(() => {}),
    );
    renderPage();

    selectViaInput(makeFile());
    await screen.findByText('colonoscopy_frame_001.png');

    fireEvent.click(submitButton());

    await waitFor(() => {
      expect(screen.getByText(/uploading image to the inference service/i)).toBeTruthy();
    });
    expect(submitButton().disabled).toBe(true);
    expect(screen.getByRole('button', { name: /uploading image/i })).toBeTruthy();
    expect(mockedCreateAnalysis).toHaveBeenCalledTimes(1);
  });

  it('kegagalan API menampilkan pesan server dan pengguna tetap di halaman', async () => {
    mockedCreateAnalysis.mockRejectedValueOnce(new Error('Server rejected this image.'));
    renderPage();

    selectViaInput(makeFile());
    await screen.findByText('colonoscopy_frame_001.png');

    fireEvent.click(submitButton());

    expect(await screen.findByText('Server rejected this image.')).toBeTruthy();
    expect(screen.queryByText('Analysis Result Page')).toBeNull();
    // Berkas tetap terpilih agar pengguna dapat mencoba ulang.
    expect(screen.getByText('colonoscopy_frame_001.png')).toBeTruthy();
    expect(submitButton().disabled).toBe(false);
    expect(mockedCreateAnalysis).toHaveBeenCalledTimes(1);
  });

  it('B4: penolakan NOT_COLONOSCOPY_IMAGE memprioritaskan pesan dari server', async () => {
    const serverMsg =
      'Citra tidak sesuai dengan karakteristik citra kolonoskopi. Silakan unggah citra kolonoskopi yang valid.';
    mockedCreateAnalysis.mockRejectedValueOnce(
      Object.assign(new Error(serverMsg), { code: 'NOT_COLONOSCOPY_IMAGE' }),
    );
    renderPage();

    selectViaInput(makeFile());
    await screen.findByText('colonoscopy_frame_001.png');

    fireEvent.click(submitButton());

    expect(await screen.findByText(serverMsg)).toBeTruthy();
    expect(screen.queryByText('Analysis Result Page')).toBeNull();
    expect(screen.getByText('colonoscopy_frame_001.png')).toBeTruthy();
    expect(submitButton().disabled).toBe(false);
  });

  it('B4: penolakan NOT_COLONOSCOPY_IMAGE dengan error non-Error menggunakan fallback baku', async () => {
    const fallbackMsg =
      'Citra tidak sesuai dengan karakteristik citra kolonoskopi. Silakan unggah citra kolonoskopi yang valid.';
    mockedCreateAnalysis.mockRejectedValueOnce({ code: 'NOT_COLONOSCOPY_IMAGE' });
    renderPage();

    selectViaInput(makeFile());
    await screen.findByText('colonoscopy_frame_001.png');

    fireEvent.click(submitButton());

    expect(await screen.findByText(fallbackMsg)).toBeTruthy();
  });

  it('B4: penolakan UNCERTAIN_COLONOSCOPY_IMAGE memprioritaskan pesan dari server', async () => {
    const serverMsg =
      'Validasi citra belum dapat diselesaikan. Silakan coba lagi beberapa saat.';
    mockedCreateAnalysis.mockRejectedValueOnce(
      Object.assign(new Error(serverMsg), { code: 'UNCERTAIN_COLONOSCOPY_IMAGE' }),
    );
    renderPage();

    selectViaInput(makeFile());
    await screen.findByText('colonoscopy_frame_001.png');

    fireEvent.click(submitButton());

    expect(await screen.findByText(serverMsg)).toBeTruthy();
    expect(screen.queryByText('Sistem tidak dapat memastikan')).toBeNull();
    expect(screen.getByText('colonoscopy_frame_001.png')).toBeTruthy();
    expect(submitButton().disabled).toBe(false);
  });

  it('B4: penolakan UNCERTAIN_COLONOSCOPY_IMAGE dengan error non-Error menggunakan fallback baku konsisten', async () => {
    const fallbackMsg =
      'Validasi citra belum dapat diselesaikan. Silakan coba lagi beberapa saat.';
    mockedCreateAnalysis.mockRejectedValueOnce({ code: 'UNCERTAIN_COLONOSCOPY_IMAGE' });
    renderPage();

    selectViaInput(makeFile());
    await screen.findByText('colonoscopy_frame_001.png');

    fireEvent.click(submitButton());

    expect(await screen.findByText(fallbackMsg)).toBeTruthy();
    expect(screen.queryByText('Sistem tidak dapat memastikan')).toBeNull();
  });

  it('berhasil memanggil createAnalysis dan menavigasi setelah backend mengonfirmasi terminal', async () => {
    // P-04: POST menjawab 202 (diterima, belum selesai) — navigasi ke halaman
    // hasil hanya terjadi setelah GET mengembalikan status terminal backend.
    mockedCreateAnalysis.mockResolvedValue({
      analysis_id: 'analysis-77',
      status: 'processing',
    });
    mockedGetAnalysis.mockResolvedValue(makeDetail('completed'));
    renderPage();

    selectViaInput(makeFile());
    await screen.findByText('colonoscopy_frame_001.png');

    fireEvent.click(submitButton());

    expect(await screen.findByText('Analysis Result Page')).toBeTruthy();
    expect(mockedCreateAnalysis).toHaveBeenCalledTimes(1);
    expect(mockedCreateAnalysis).toHaveBeenCalledWith(expect.any(File));
    // Polling memakai analysis_id dari respons 202.
    expect(mockedGetAnalysis).toHaveBeenCalledWith('analysis-77');
  });
});

describe('NewAnalysis — progres P-04 (202, QUEUE_FULL, polling berurutan)', () => {
  /** Siapkan berkas lalu tekan Start — kondisi awal semua tes progres. */
  async function selectAndSubmit(): Promise<void> {
    selectViaInput(makeFile());
    await screen.findByText('colonoscopy_frame_001.png');
    fireEvent.click(submitButton());
  }

  /** Kuras rantai mikrotask di dalam act agar state & effect ter-commit. */
  async function flushMicrotasks(): Promise<void> {
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });
  }

  it('respons 202 membawa analysis_id dan status processing — belum dianggap selesai', async () => {
    mockedCreateAnalysis.mockResolvedValue({
      analysis_id: 'analysis-77',
      status: 'processing',
    });
    mockedGetAnalysis.mockResolvedValue(makeDetail('processing'));
    renderPage();

    await selectAndSubmit();

    // Panel progres tampil begitu backend menerima (202); polling memakai ID itu.
    expect(await screen.findByTestId('analysis-progress')).toBeTruthy();
    expect(mockedCreateAnalysis).toHaveBeenCalledTimes(1);
    expect(mockedGetAnalysis).toHaveBeenCalledWith('analysis-77');

    // Status 'processing' berarti belum selesai: tidak navigasi, tidak klaim selesai.
    expect(screen.queryByText('Analysis Result Page')).toBeNull();
    expect(screen.queryByText(/analysis (is )?(complete|finished)/i)).toBeNull();
    expect(screen.queryByRole('progressbar')).toBeNull();
  });

  it('HTTP 429 QUEUE_FULL menampilkan pesan yang jelas dan pengguna dapat mencoba lagi', async () => {
    mockedCreateAnalysis.mockRejectedValue(
      Object.assign(new Error('Analysis queue is at capacity. Please try again shortly.'), {
        code: 'QUEUE_FULL',
      }),
    );
    renderPage();

    await selectAndSubmit();

    expect(
      await screen.findByText('The analysis queue is full. Please try again in a moment.'),
    ).toBeTruthy();
    // Pesan mentah backend tidak duplikat; pengguna tetap di halaman unggah.
    expect(screen.queryByText(/at capacity/i)).toBeNull();
    expect(screen.queryByText('Analysis Result Page')).toBeNull();
    expect(screen.queryByTestId('analysis-progress')).toBeNull();
    expect(screen.getByText('colonoscopy_frame_001.png')).toBeTruthy();
    expect(submitButton().disabled).toBe(false);
    // Tanpa penerimaan tidak ada polling sama sekali.
    expect(mockedGetAnalysis).not.toHaveBeenCalled();
    expect(mockedCreateAnalysis).toHaveBeenCalledTimes(1);
  });

  it('persentase valid dari backend dirender apa adanya (progressbar + fase)', async () => {
    mockedCreateAnalysis.mockResolvedValue({
      analysis_id: 'analysis-77',
      status: 'processing',
    });
    mockedGetAnalysis.mockResolvedValue(
      makeDetail('processing', { current_step: 'inference', progress_percent: 42 }),
    );
    renderPage();

    await selectAndSubmit();

    expect(await screen.findByText('42%')).toBeTruthy();
    const bar = screen.getByRole('progressbar', { name: 'Analysis progress' });
    expect(bar.getAttribute('aria-valuenow')).toBe('42');
    expect(screen.getByText(/current phase: inference/i)).toBeTruthy();
  });

  it('current_step tanpa persentase tetap tampil tanpa angka buatan', async () => {
    mockedCreateAnalysis.mockResolvedValue({
      analysis_id: 'analysis-77',
      status: 'processing',
    });
    mockedGetAnalysis.mockResolvedValue(
      makeDetail('processing', { current_step: 'postprocessing' }),
    );
    const { container } = renderPage();

    await selectAndSubmit();

    expect(await screen.findByText(/current phase: postprocessing/i)).toBeTruthy();
    expect(screen.queryByRole('progressbar')).toBeNull();
    expect(container.textContent).not.toMatch(/\d+%/);
  });

  it('tanpa field progres sama sekali menampilkan pesan persiapan, bukan persentase', async () => {
    mockedCreateAnalysis.mockResolvedValue({
      analysis_id: 'analysis-77',
      status: 'processing',
    });
    mockedGetAnalysis.mockResolvedValue(makeDetail('processing'));
    const { container } = renderPage();

    await selectAndSubmit();

    expect(
      await screen.findByText('Preparing analysis progress. This may take a moment.'),
    ).toBeTruthy();
    expect(screen.queryByRole('progressbar')).toBeNull();
    expect(container.textContent).not.toMatch(/\d+%/);
  });

  it('persentase di luar rentang kontrak tidak dirender sebagai angka', async () => {
    mockedCreateAnalysis.mockResolvedValue({
      analysis_id: 'analysis-77',
      status: 'processing',
    });
    mockedGetAnalysis.mockResolvedValue(
      makeDetail('processing', { current_step: 'gradcam', progress_percent: 150 }),
    );
    const { container } = renderPage();

    await selectAndSubmit();

    expect(await screen.findByText(/current phase: gradcam/i)).toBeTruthy();
    expect(screen.queryByRole('progressbar')).toBeNull();
    expect(container.textContent).not.toMatch(/\d+%/);
  });

  it('polling berlanjut melewati 12 respons processing lalu berhenti setelah completed', async () => {
    mockedCreateAnalysis.mockResolvedValue({
      analysis_id: 'analysis-77',
      status: 'processing',
    });
    // 13 respons pertama tetap processing; respons keempat belas completed.
    let calls = 0;
    mockedGetAnalysis.mockImplementation(async () => {
      calls += 1;
      return makeDetail(calls <= 13 ? 'processing' : 'completed');
    });
    renderPage();

    selectViaInput(makeFile());
    await screen.findByText('colonoscopy_frame_001.png');
    vi.useFakeTimers();
    fireEvent.click(submitButton());
    await flushMicrotasks();

    expect(screen.getByTestId('analysis-progress')).toBeTruthy();
    expect(calls).toBe(1);

    // Jendela besar: polling berjalan terus selama status masih processing.
    await act(async () => { await vi.advanceTimersByTimeAsync(120000); });

    // Lewati batas lama 12 percobaan → respons ke-14 (terminal) → navigasi,
    // lalu polling berhenti tepat di situ.
    expect(calls).toBe(14);
    expect(screen.getByText('Analysis Result Page')).toBeTruthy();

    await act(async () => { await vi.advanceTimersByTimeAsync(30000); });
    expect(calls).toBe(14);
    // Polling GET tidak pernah mengirim ulang file (POST hanya sekali).
    expect(mockedCreateAnalysis).toHaveBeenCalledTimes(1);
  });

  it('polling berhenti pada status failed dan membuka halaman hasil', async () => {
    mockedCreateAnalysis.mockResolvedValue({
      analysis_id: 'analysis-77',
      status: 'processing',
    });
    mockedGetAnalysis.mockResolvedValueOnce(makeDetail('processing'));
    mockedGetAnalysis.mockResolvedValue(makeDetail('failed'));
    renderPage();

    selectViaInput(makeFile());
    await screen.findByText('colonoscopy_frame_001.png');
    vi.useFakeTimers();
    fireEvent.click(submitButton());
    await flushMicrotasks();

    expect(mockedGetAnalysis).toHaveBeenCalledTimes(1);

    // Jendela besar: respons kedua (terminal) menghentikan polling.
    await act(async () => { await vi.advanceTimersByTimeAsync(120000); });
    // Status terminal backend dikonfirmasi → halaman hasil, polling selesai.
    expect(screen.getByText('Analysis Result Page')).toBeTruthy();
    expect(mockedGetAnalysis).toHaveBeenCalledTimes(2);

    await act(async () => { await vi.advanceTimersByTimeAsync(30000); });
    expect(mockedGetAnalysis).toHaveBeenCalledTimes(2);
  });

  it('kegagalan jaringan sementara bukan terminal dan tidak mengirim ulang file', async () => {
    mockedCreateAnalysis.mockResolvedValue({
      analysis_id: 'analysis-77',
      status: 'processing',
    });
    mockedGetAnalysis.mockRejectedValueOnce(new Error('Network error'));
    mockedGetAnalysis.mockResolvedValue(makeDetail('completed'));
    renderPage();

    selectViaInput(makeFile());
    await screen.findByText('colonoscopy_frame_001.png');
    vi.useFakeTimers();
    fireEvent.click(submitButton());
    await flushMicrotasks();

    // Pemberitahuan sementara tampil, status analisis tidak diubah menjadi gagal.
    expect(
      screen.getByText(/connection issue while checking progress/i),
    ).toBeTruthy();
    expect(screen.queryByText('Analysis Result Page')).toBeNull();
    expect(mockedCreateAnalysis).toHaveBeenCalledTimes(1);

    // Jadwal retry berjalan; panggilan berikutnya memulihkan tampilan lalu
    // status terminal menghentikan polling (berhenti tepat di dua panggilan).
    await act(async () => { await vi.advanceTimersByTimeAsync(120000); });
    expect(mockedGetAnalysis).toHaveBeenCalledTimes(2);
    expect(screen.getByText('Analysis Result Page')).toBeTruthy();
    // Percobaan ulang tidak membuat analisis baru atau mengirim ulang file.
    expect(mockedCreateAnalysis).toHaveBeenCalledTimes(1);
  });
});
