import React, { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import {
  AlertCircle,
  ArrowLeft,
  FileCheck2,
  Image as ImageIcon,
  Info,
  Loader2,
  UploadCloud,
  X,
} from 'lucide-react';
import { createAnalysis, getAnalysis, ApiRequestError, REQUEST_TIMEOUT_ERROR_CODE } from '@/utils/analysis';

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ALLOWED_MIME_TYPES = new Set(['image/jpeg', 'image/png']);

/** Polling progres setelah backend menerima analisis (HTTP 202). */
const PROGRESS_POLL_INTERVAL_MS = 2000;
/**
 * Batas maksimum percobaan polling (default: ~10 menit pada interval 2 s).
 *
 * Batas waktu tunggu yang wajar untuk pipeline inferensi PIXEL-T (U-Net +
 * ResNet50, Grad-CAM, upload artefak). Ketika batas tercapai tanpa status
 * terminal backend, polling dihentikan dan pengguna diberi tahu; analisis
 * yang sedang berjalan TIDAK dinyatakan gagal dan hasil tersimpan tidak
 * pernah dihapus.
 */
export const PROGRESS_POLL_MAX_ATTEMPTS = 300;

/** HTTP 429 QUEUE_FULL (APIContract §12) — pesan jelas untuk pengguna. */
const QUEUE_FULL_MESSAGE = 'The analysis queue is full. Please try again in a moment.';
/**
 * Ekstensi yang diterima (`.jpg`, `.jpeg`, `.png`) beserta MIME type yang
 * harus disandingkannya; kunci record sekaligus menjadi daftar ekstensi.
 */
const EXPECTED_MIME_BY_EXTENSION: Readonly<Record<string, string>> = {
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.png': 'image/png',
};

/**
 * Spesifikasi pipeline yang ditampilkan pada panel kanan atas. Setiap nilai
 * mengikuti konstanta validasi di bawah — bukan angka yang dikarang.
 */
const PIPELINE_SPECS: ReadonlyArray<{ label: string; value: string }> = [
  { label: 'Inference model', value: 'U-Net + ResNet50' },
  { label: 'Input format', value: 'JPG, JPEG, PNG' },
  { label: 'Max file size', value: '10 MB' },
];

/**
 * Tiga langkah "What happens next?" (referensi desain), disunting agar hanya
 * berisi perilaku yang benar-benar dimiliki aplikasi:
 *   - tanpa klaim metrik IoU/Dice per citra (tidak ada fieldnya pada API —
 *     lihat APIContract §15 dan `AnalysisDetail`),
 *   - tanpa "clinician verification" (status verifikasi tidak punya sumber),
 *   - tanpa fitur cetak/ekspor rekam medis (tidak ada di spec maupun kode).
 */
const NEXT_STEPS: ReadonlyArray<{ title: string; body: string }> = [
  {
    title: 'Image format validation',
    body: 'The system checks the file format (JPG, JPEG, PNG), the 10 MB size limit, the decoded image dimensions, and the integrity of the colonoscopy image buffer before it is sent to the inference service.',
  },
  {
    title: 'U-Net segmentation & Grad-CAM',
    body: 'The U-Net + ResNet50 model maps the contours of polyp lesions while Grad-CAM highlights the internal activations behind that segmentation output.',
  },
  {
    title: 'Results & saved sessions',
    body: 'Segmentation results are presented side-by-side with a Grad-CAM overlay, model analysis, a non-diagnostic summary, and a clinical disclaimer — and every saved session can be revisited from History.',
  },
];

/**
 * Format yang diterima: ekstensi `.jpg`/`.jpeg`/`.png` plus MIME type yang
 * harus disandingkannya; kunci record sekaligus menjadi daftar ekstensi.
 */
function validateFile(file: File): string | null {
  const dotIndex = file.name.lastIndexOf('.');
  const extension = dotIndex >= 0 ? file.name.slice(dotIndex).toLowerCase() : '';
  const expectedMime = EXPECTED_MIME_BY_EXTENSION[extension];
  if (!expectedMime) {
    return 'Select a JPG, JPEG, or PNG image.';
  }
  if (file.type && file.type !== expectedMime) {
    return ALLOWED_MIME_TYPES.has(file.type)
      ? 'The file extension and image type do not match. Choose a JPG, JPEG, or PNG file.'
      : 'Select a JPG, JPEG, or PNG image.';
  }
  if (file.size === 0) {
    return 'The image file is empty. Choose another file.';
  }
  if (file.size > MAX_FILE_SIZE) {
    return 'File size exceeds the 10 MB limit.';
  }
  if (
    file.name.includes('..') ||
    /[\\/]/.test(file.name) ||
    /[\u0000-\u001f\u007f]/.test(file.name)
  ) {
    return 'Invalid file name.';
  }
  return null;
}

function formatFileSize(size: number): string {
  return size < 1024 * 1024
    ? `${(size / 1024).toFixed(1)} KB`
    : `${(size / (1024 * 1024)).toFixed(2)} MB`;
}

/**
 * Persentase progres yang sah menurut kontrak (APIContract §12): bilangan
 * bulat 0–100. Null, undefined, string, atau nilai di luar rentang dianggap
 * "belum tersedia" — tidak pernah ditampilkan sebagai angka buatan.
 */
function validProgressPercent(value: unknown): number | null {
  return typeof value === 'number' && Number.isInteger(value) && value >= 0 && value <= 100
    ? value
    : null;
}

/** `artifact_composition` → `artifact composition` (token kontrak tetap asli). */
function formatStep(step: string): string {
  return step.replace(/_/g, ' ');
}

export const NewAnalysis: React.FC = () => {
  const navigate = useNavigate();
  const fileInput = useRef<HTMLInputElement>(null);
  const validationRun = useRef(0);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState('');
  const [validationError, setValidationError] = useState('');
  const [serverError, setServerError] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  /** analysis_id dari respons 202; null sampai backend menerima unggahan. */
  const [acceptedId, setAcceptedId] = useState<string | null>(null);
  /** Snapshot progres GET terbaru; field hilang = belum tersedia (tidak dikarang). */
  const [progress, setProgress] = useState<{
    current_step?: string;
    progress_percent?: number;
  } | null>(null);
  const [progressNotice, setProgressNotice] = useState('');

  useEffect(() => {
    if (!file) {
      setPreviewUrl('');
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  /**
   * Polling progres setelah analisis diterima (HTTP 202, APIContract §12).
   *
   * Berhenti pada status terminal backend (`completed`/`failed`), saat
   * komponen dilepas, saat sesi berakhir, saat server menjawab dengan error
   * terstruktur, atau ketika `PROGRESS_POLL_MAX_ATTEMPTS` tercapai. Kegagalan
   * jaringan/timeout sementara bukan status terminal dan tidak mengubah status
   * analisis. Polling berurutan: jadwal berikutnya dibuat setelah respons
   * selesai, sehingga tidak pernah tumpang tindih, dan timer dibersihkan saat
   * unmount. Navigasi ke halaman hasil hanya terjadi setelah backend
   * mengonfirmasi status terminal.
   */
  useEffect(() => {
    if (!acceptedId) return undefined;
    let cancelled = false;
    let inFlight = false;
    let timeoutId: number | undefined;
    let pollCount = 0;

    const poll = async () => {
      if (cancelled || inFlight) return;
      if (pollCount >= PROGRESS_POLL_MAX_ATTEMPTS) {
        // Batas maksimum tercapai tanpa status terminal: hentikan polling.
        // Analisis tetap berjalan di backend; pengguna dapat memeriksa hasil
        // di halaman riwayat. Ini BUKAN kegagalan segmentasi.
        cancelled = true;
        setProgressNotice(
          'This analysis is still running. You can leave this page and check your history later for the result.',
        );
        return;
      }
      inFlight = true;
      const pollStart = performance.now();
      pollCount++;
      try {
        console.debug(`[CORRELATION] analysis_id=${acceptedId} stage=polling poll=${pollCount} start`);
        const detail = await getAnalysis(acceptedId);
        const pollDur = performance.now() - pollStart;
        console.debug(`[CORRELATION] analysis_id=${acceptedId} stage=polling poll=${pollCount} end duration_ms=${pollDur.toFixed(1)} status=${detail.analysis.status}`);
        if (cancelled) return;
        setProgress({
          current_step: detail.analysis.current_step,
          progress_percent: detail.analysis.progress_percent,
        });
        setProgressNotice('');
        const status = detail.analysis.status;
        if (status === 'completed' || status === 'failed') {
          // Terminal backend dikonfirmasi: hentikan polling lalu buka hasil.
          cancelled = true;
          navigate(`/analysis/${encodeURIComponent(acceptedId)}`);
          return;
        }
        timeoutId = window.setTimeout(() => {
          void poll();
        }, PROGRESS_POLL_INTERVAL_MS);
      } catch (error) {
        if (cancelled) return;
        // Jika error 401 (Unauthorized), hentikan polling dan minta login ulang.
        if (error instanceof Error && error.message.includes('Sesi Anda telah berakhir')) {
          cancelled = true;
          if (timeoutId !== undefined) window.clearTimeout(timeoutId);
          setServerError('Sesi Anda telah berakhir. Silakan masuk kembali untuk melanjutkan.');
          return;
        }
        // Respons server terstruktur selain timeout: bukan gangguan jaringan, jadi
        // berhenti total dan laporkan pesan ke pengguna (mis. analisis tidak ditemukan).
        if (
          error instanceof ApiRequestError &&
          error.code !== REQUEST_TIMEOUT_ERROR_CODE
        ) {
          cancelled = true;
          if (timeoutId !== undefined) window.clearTimeout(timeoutId);
          setProgressNotice(
            error.message || 'Server could not return the analysis progress.',
          );
          return;
        }
        // Kegagalan jaringan/timeout sementara: tetap polling dalam batas
        // maksimum percobaan (`PROGRESS_POLL_MAX_ATTEMPTS`).
        setProgressNotice('Connection issue while checking progress. Retrying...');
        timeoutId = window.setTimeout(() => {
          void poll();
        }, PROGRESS_POLL_INTERVAL_MS);
      } finally {
        inFlight = false;
      }
    };

    void poll();

    return () => {
      cancelled = true;
      if (timeoutId !== undefined) window.clearTimeout(timeoutId);
    };
  }, [acceptedId, navigate]);

  const selectFile = async (selectedFile?: File) => {
    setServerError('');
    setValidationError('');
    if (!selectedFile) return;
    const run = ++validationRun.current;
    setFile(null);
    setIsValidating(true);
    let error = validateFile(selectedFile);
    if (!error) {
      try {
        const decoded = await createImageBitmap(selectedFile);
        if (decoded.width <= 0 || decoded.height <= 0) {
          error = 'Invalid image dimensions.';
        }
        decoded.close();
      } catch {
        error = 'This file cannot be read as a JPG, JPEG, or PNG image.';
      }
    }
    if (run !== validationRun.current) return;
    setValidationError(error || '');
    setFile(error ? null : selectedFile);
    setIsValidating(false);
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file || isUploading || acceptedId) return;
    setServerError('');
    setIsUploading(true);
    try {
      const created = await createAnalysis(file);
      // HTTP 202 hanya berisi analysis_id + status 'processing': pekerjaan
      // BELUM selesai, jadi tampilkan panel progres (polling) alih-alih
      // mengklaim hasil. Navigasi menunggu konfirmasi terminal backend.
      setAcceptedId(created.analysis_id);
    } catch (error) {
      const code = (error as { code?: unknown } | null)?.code;
      if (code === 'NOT_COLONOSCOPY_IMAGE') {
        setServerError(
          error instanceof Error
            ? error.message
            : 'Citra tidak sesuai dengan karakteristik citra kolonoskopi. Silakan unggah citra kolonoskopi yang valid.'
        );
      } else if (code === 'UNCERTAIN_COLONOSCOPY_IMAGE') {
        setServerError(
          error instanceof Error
            ? error.message
            : 'Validasi citra belum dapat diselesaikan. Silakan coba lagi beberapa saat.'
        );
      } else if (code === 'QUEUE_FULL') {
        setServerError(QUEUE_FULL_MESSAGE);
      } else {
        setServerError(
          error instanceof Error ? error.message : 'Image upload failed. Please try again.'
        );
      }
    } finally {
      setIsUploading(false);
    }
  };

  const removeSelectedFile = () => {
    validationRun.current += 1;
    setFile(null);
    setIsValidating(false);
    setValidationError('');
    setServerError('');
  };

  /**
   * Baris status mengikuti referensi. Semua nilai diturunkan dari state
   * sesungguhnya — tidak ada teks kemajuan yang dikarang.
   */
  const statusMessage = isUploading
    ? 'Uploading image to the inference service...'
    : isValidating
      ? 'Validating selected image file...'
      : file
        ? 'Image file ready for inference.'
        : 'Awaiting colonoscopy image files...';

  const statusHint = isUploading
    ? 'Please keep this tab open until the upload completes'
    : isValidating
      ? 'Checking format, size, and image dimensions'
      : file
        ? 'Ready to begin inference'
        : 'Select an image file first to begin inference';

  // Hanya angka backend yang valid (integer 0–100) yang dirender; selain itu
  // panel menampilkan fase/status yang tersedia tanpa persentase karangan.
  const percent = validProgressPercent(progress?.progress_percent);
  const step =
    typeof progress?.current_step === 'string' && progress.current_step.length > 0
      ? progress.current_step
      : null;

  const startDisabled = !file || isUploading || isValidating || acceptedId !== null;

  return (
    <div className="space-y-6">
      {/* Breadcrumb + judul + panel spesifikasi pipeline (referensi) */}
      <div className="space-y-5 border-b border-neutral-200 pb-8 dark:border-dark-border">
        <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2 text-xs">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-1 text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200"
          >
            <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" /> Back to Dashboard
          </Link>
          <span className="text-neutral-300 dark:text-neutral-700" aria-hidden="true">
            /
          </span>
          <span className="font-medium text-neutral-800 dark:text-dark-text">New Analysis</span>
        </nav>

        <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
          <div className="space-y-3">
            <h1 className="text-3xl font-bold uppercase tracking-tight text-neutral-900 sm:text-4xl dark:text-dark-text">
              New Analysis
            </h1>
            <p className="max-w-2xl text-sm leading-relaxed text-neutral-600 dark:text-dark-textMuted">
              Upload a single colonoscopy image for colorectal polyp segmentation inference
              (U-Net + ResNet50) and Grad-CAM visual explanation.
            </p>
          </div>

          <div
            data-testid="pipeline-spec"
            className="w-full rounded-lg border border-neutral-200 bg-white dark:border-dark-border dark:bg-dark-surface"
          >
            <div className="border-b border-neutral-100 px-4 py-3 dark:border-dark-border">
              <span className="font-mono text-[11px] font-semibold uppercase tracking-wider text-neutral-600 dark:text-dark-textMuted">
                Pipeline specification
              </span>
            </div>
            <dl className="divide-y divide-neutral-100 dark:divide-dark-border">
              {PIPELINE_SPECS.map((spec) => (
                <div
                  key={spec.label}
                  className="flex items-center justify-between gap-3 px-4 py-3"
                >
                  <dt className="font-mono text-[10px] uppercase tracking-wider text-neutral-600 dark:text-dark-textMuted">
                    {spec.label}
                  </dt>
                  <dd className="font-mono text-xs font-bold uppercase tracking-wide text-badgeText-accent dark:text-accent-500">
                    {spec.value}
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>

      {acceptedId ? (
        <section
          data-testid="analysis-progress"
          role="status"
          aria-live="polite"
          className="space-y-4 rounded-lg border border-neutral-200 bg-white p-5 dark:border-dark-border dark:bg-dark-surface"
        >
          <div className="flex items-start gap-3">
            <Loader2
              className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-accent-700 dark:text-accent-500"
              aria-hidden="true"
            />
            <div className="min-w-0 space-y-1">
              <p className="text-sm font-semibold text-neutral-900 dark:text-dark-text">
                Analysis accepted. The AI pipeline is running in the background.
              </p>
              <p className="text-xs leading-relaxed text-neutral-600 dark:text-dark-textMuted">
                This page advances when the backend reports a terminal status.
              </p>
            </div>
          </div>

          {percent !== null && (
            <div className="space-y-1.5">
              <div
                role="progressbar"
                aria-label="Analysis progress"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={percent}
                className="h-2 w-full max-w-md overflow-hidden rounded-full bg-neutral-200 dark:bg-dark-elevated"
              >
                <div
                  className="h-full rounded-full bg-accent-700 dark:bg-accent-500 transition-all"
                  style={{ width: `${percent}%` }}
                />
              </div>
              <p className="font-mono text-xs font-semibold text-neutral-700 dark:text-dark-text">
                {percent}%
              </p>
            </div>
          )}

          {step ? (
            <p className="text-xs text-neutral-600 dark:text-dark-textMuted">
              <span className="font-semibold uppercase tracking-wide">
                Current phase: {formatStep(step)}
              </span>
            </p>
          ) : percent === null ? (
            <p className="text-xs text-neutral-600 dark:text-dark-textMuted">
              Preparing analysis progress. This may take a moment.
            </p>
          ) : null}

          {progressNotice && (
            <p className="text-xs text-neutral-600 dark:text-dark-textMuted">{progressNotice}</p>
          )}
        </section>
      ) : (
      <form className="space-y-5" onSubmit={handleSubmit}>
        {/* Area unggah — garis putus-putus teal sesuai referensi */}
        <Card
          variant="bordered"
          className={`overflow-hidden border-2 border-dashed transition-colors ${
            isDragging ? '!border-accent-700 ring-2 ring-accent-600/40' : '!border-accent-600'
          }`}
        >
          <div
            data-testid="drop-zone"
            className="px-6 py-12 text-center sm:py-16"
            onDragEnter={(event) => {
              event.preventDefault();
              setIsDragging(true);
            }}
            onDragOver={(event) => event.preventDefault()}
            onDragLeave={(event) => {
              if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
                setIsDragging(false);
              }
            }}
            onDrop={(event) => {
              event.preventDefault();
              setIsDragging(false);
              void selectFile(event.dataTransfer.files[0]);
            }}
          >
            <input
              ref={fileInput}
              className="sr-only"
              type="file"
              accept="image/jpeg,image/png,.jpg,.jpeg,.png"
              aria-label="Select endoscopy image file"
              onChange={(event) => {
                void selectFile(event.currentTarget.files?.[0]);
                event.currentTarget.value = '';
              }}
            />

            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-lg bg-neutral-100 text-accent-700 dark:bg-dark-elevated dark:text-accent-500">
              <UploadCloud className="h-7 w-7" aria-hidden="true" />
            </div>

            <div className="mx-auto mt-5 max-w-md space-y-2">
              <h2 className="text-lg font-bold uppercase tracking-wide text-neutral-900 sm:text-xl dark:text-dark-text">
                Select endoscopy image
              </h2>
              <p className="text-sm leading-relaxed text-neutral-600 dark:text-dark-textMuted">
                Drag and drop image files directly into this area, or use the browse button
                below.
              </p>
            </div>

            <div className="mt-5 flex justify-center">
              <Button
                type="button"
                variant="outline"
                className="!border-accent-600 uppercase tracking-wide"
                leftIcon={<ImageIcon className="h-4 w-4" aria-hidden="true" />}
                onClick={() => fileInput.current?.click()}
              >
                Select file
              </Button>
            </div>
          </div>

          {file && previewUrl && (
            <div className="grid gap-5 border-t border-neutral-200 bg-neutral-50 p-4 dark:border-dark-border dark:bg-dark-surface sm:grid-cols-[minmax(0,1fr)_220px] sm:p-5">
              <div className="min-w-0 self-center space-y-3">
                <div className="flex items-start gap-3">
                  <FileCheck2
                    className="mt-0.5 h-5 w-5 shrink-0 text-accent-700 dark:text-accent-500"
                    aria-hidden="true"
                  />
                  <div className="min-w-0 flex-1">
                    <p className="break-all text-sm font-semibold text-neutral-900 dark:text-dark-text">
                      {file.name}
                    </p>
                    <p className="mt-1 text-xs text-neutral-600 dark:text-dark-textMuted">
                      {formatFileSize(file.size)} &middot; {file.type}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    aria-label="Remove selected image"
                    onClick={removeSelectedFile}
                  >
                    <X className="h-4 w-4" aria-hidden="true" />
                  </Button>
                </div>
              </div>
              <img
                src={previewUrl}
                alt={`Preview ${file.name}`}
                className="max-h-56 w-full rounded-sm border border-neutral-200 bg-black object-contain dark:border-dark-border"
              />
            </div>
          )}
        </Card>

        {validationError && (
          <p role="alert" className="flex items-start gap-2 text-sm text-badgeText-error dark:text-badgeText-error-dark">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />{' '}
            {validationError}
          </p>
        )}
        {serverError && (
          <p role="alert" className="flex items-start gap-2 rounded-md border border-semantic-error/30 bg-semantic-error/5 p-3 text-sm text-badgeText-error dark:text-badgeText-error-dark">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" /> {serverError}
          </p>
        )}

        {/* Baris status + tombol START ANALYSIS (referensi) */}
        <div className="flex flex-col gap-4 rounded-lg border border-neutral-200 bg-neutral-50 p-4 dark:border-dark-border dark:bg-dark-elevated sm:flex-row sm:items-center sm:justify-between sm:gap-6">
          <div className="flex min-w-0 items-center gap-2.5">
            <span
              aria-hidden="true"
              className="h-2.5 w-2.5 shrink-0 rounded-sm bg-accent-600 dark:bg-accent-500"
            />
            <p className="min-w-0 text-sm text-neutral-700 dark:text-dark-text">
              <span className="font-semibold uppercase tracking-wide">Status:</span>{' '}
              {statusMessage}
            </p>
          </div>

          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
            <p className="text-xs text-neutral-600 dark:text-dark-textMuted sm:text-right">
              {statusHint}
            </p>
            <Button
              type="submit"
              className="uppercase tracking-wide"
              disabled={startDisabled}
              isLoading={isUploading || isValidating}
            >
              {isUploading
                ? 'Uploading image...'
                : isValidating
                  ? 'Validating image...'
                  : 'Start analysis'}
            </Button>
          </div>
        </div>
      </form>
      )}

      {/* WHAT HAPPENS NEXT? — tiga langkah alur kerja */}
      <section
        data-testid="next-steps"
        aria-labelledby="what-happens-next-heading"
        className="rounded-lg border border-neutral-200 bg-white dark:border-dark-border dark:bg-dark-surface"
      >
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-neutral-100 px-5 py-4 dark:border-dark-border">
          <h2
            id="what-happens-next-heading"
            className="flex items-center gap-2 text-base font-bold uppercase tracking-wide text-neutral-900 dark:text-dark-text"
          >
            <Info className="h-4 w-4 shrink-0 text-accent-600 dark:text-accent-500" aria-hidden="true" />
            What happens next?
          </h2>
          <span className="font-mono text-[10px] uppercase tracking-wider text-neutral-600 dark:text-dark-textMuted">
            Clinical workflow guidelines
          </span>
        </div>

        <div className="grid grid-cols-1 divide-y divide-neutral-100 dark:divide-dark-border lg:grid-cols-3 lg:divide-x lg:divide-y-0">
          {NEXT_STEPS.map((step, index) => (
            <div key={step.title} className="p-5">
              <div className="flex items-center gap-2.5">
                <span
                  aria-hidden="true"
                  className="inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-accent-600 text-[11px] font-bold text-neutral-950 dark:bg-accent-500"
                >
                  {index + 1}
                </span>
                <h3 className="text-xs font-bold uppercase tracking-wide text-neutral-900 sm:text-sm dark:text-dark-text">
                  {step.title}
                </h3>
              </div>
              <p className="mt-2.5 text-sm leading-relaxed text-neutral-600 dark:text-dark-textMuted">
                {step.body}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default NewAnalysis;