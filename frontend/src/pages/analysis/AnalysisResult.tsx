import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Activity, AlertCircle, ArrowLeft, History as HistoryIcon, ImageOff, Loader2 } from 'lucide-react';
import { getAnalysis, type AnalysisDetail, type AnalysisStatus } from '@/services/analysis';

const POLL_INTERVAL_MS = 5000;
const MAX_POLL_ATTEMPTS = 12;

interface ImagePanelProps {
  title: string;
  url?: string | null;
  alt: string;
  unavailableMessage: string;
  onImageError: () => void;
  imageFailed?: boolean;
}

const ImagePanel: React.FC<ImagePanelProps> = ({
  title,
  url,
  alt,
  unavailableMessage,
  onImageError,
  imageFailed = false,
}) => (
  <Card className="min-w-0 p-3 sm:p-4">
    <h3 className="mb-3 text-sm font-semibold text-neutral-900 dark:text-dark-text">{title}</h3>
    {url && !imageFailed ? (
      <div className="flex min-h-48 items-center justify-center overflow-hidden rounded-sm border border-neutral-200 bg-black dark:border-dark-border sm:min-h-64">
        <img
          src={url}
          alt={alt}
          onError={onImageError}
          className="max-h-[65vh] w-full object-contain"
        />
      </div>
    ) : (
      <div className="flex min-h-48 flex-col items-center justify-center gap-2 rounded-sm border border-dashed border-neutral-300 bg-neutral-50 px-4 text-center dark:border-dark-border dark:bg-dark-elevated sm:min-h-64">
        <ImageOff className="h-5 w-5 text-neutral-400" aria-hidden="true" />
        <p className="max-w-sm text-sm text-neutral-600 dark:text-dark-textMuted">
          {imageFailed ? 'Image could not be loaded. Refresh to try again.' : unavailableMessage}
        </p>
      </div>
    )}
  </Card>
);

function unavailableMessage(status: AnalysisStatus, output: string): string {
  if (status === 'processing') {
    return `${output} is not available while analysis is processing.`;
  }
  if (status === 'failed') {
    return `${output} is not available for this analysis.`;
  }
  return `${output} is not available yet.`;
}

function statusVariant(status: AnalysisStatus): 'info' | 'success' | 'error' {
  if (status === 'completed') return 'success';
  if (status === 'failed') return 'error';
  return 'info';
}

export const AnalysisResult: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [analysis, setAnalysis] = useState<AnalysisDetail | null>(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [failedImages, setFailedImages] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setAnalysis(null);
    setError('');
    setIsLoading(true);
    if (!id) {
      setError('ID analisis tidak ditemukan.');
      setIsLoading(false);
      return;
    }

    let active = true;
    let requestInFlight = false;
    let pollAttempts = 0;
    let timeoutId: number | undefined;

    const refresh = async (initialRequest = false) => {
      if (!active || requestInFlight) return;
      requestInFlight = true;
      try {
        const result = await getAnalysis(id);
        if (!active) return;
        setAnalysis((previous) => {
          const previousUrl = previous?.analysis.status === 'processing'
            && result.analysis.status === 'processing'
            ? previous.input.original_image_url
            : null;
          return previousUrl
            ? { ...result, input: { ...result.input, original_image_url: previousUrl } }
            : result;
        });
        setError('');
        if (result.analysis.status === 'processing' && pollAttempts < MAX_POLL_ATTEMPTS) {
          pollAttempts += 1;
          timeoutId = window.setTimeout(() => { void refresh(); }, POLL_INTERVAL_MS);
        }
      } catch (requestError: unknown) {
        if (active) {
          setError(requestError instanceof Error ? requestError.message : 'Unable to load this analysis.');
        }
      } finally {
        requestInFlight = false;
        if (active && initialRequest) setIsLoading(false);
      }
    };

    void refresh(true);

    return () => {
      active = false;
      if (timeoutId !== undefined) window.clearTimeout(timeoutId);
    };
  }, [id]);

  const detail = analysis;
  const status = detail?.analysis.status;
  const timestamp = detail?.analysis.created_at
    ? new Date(detail.analysis.created_at).toLocaleString()
    : null;
  const modelDetails = [
    detail?.model?.architecture ? ['Architecture', detail.model.architecture] : null,
    detail?.model?.version ? ['Model version', detail.model.version] : null,
    detail?.model_analysis?.segmentation_status
      ? ['Segmentation status', detail.model_analysis.segmentation_status]
      : null,
    detail?.model_analysis?.detection_category
      ? ['Detection category', detail.model_analysis.detection_category.replace(/_/g, ' ')]
      : null,
    detail?.model_analysis?.area_pixels != null
      ? ['Area', `${detail.model_analysis.area_pixels} px`] : null,
    detail?.model_analysis?.area_ratio != null
      ? ['Area ratio', detail.model_analysis.area_ratio] : null,
    detail?.model_analysis?.bounding_width_pixels != null
      ? ['Bounding width', `${detail.model_analysis.bounding_width_pixels} px`] : null,
    detail?.model_analysis?.bounding_height_pixels != null
      ? ['Bounding height', `${detail.model_analysis.bounding_height_pixels} px`] : null,
  ].filter((item): item is [string, string | number] => item !== null);

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-neutral-200 pb-5 dark:border-dark-border">
        <div className="space-y-3">
          <Link to="/dashboard" className="inline-flex items-center gap-1 text-xs text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200">
            <ArrowLeft className="h-3.5 w-3.5" /> Dashboard
          </Link>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold text-neutral-900 dark:text-dark-text sm:text-3xl">Analysis Result</h1>
            {status && <Badge variant={statusVariant(status)}>{status}</Badge>}
          </div>
        </div>
        <div className="flex gap-2">
          <Link to="/analysis/new">
            <Button variant="outline" size="sm">Analisis baru</Button>
          </Link>
          <Link to="/history">
            <Button variant="secondary" size="sm" leftIcon={<HistoryIcon className="h-4 w-4" />}>
              Riwayat
            </Button>
          </Link>
        </div>
      </header>

      {isLoading && (
        <div role="status" className="flex items-center gap-3 py-12 text-sm text-neutral-600 dark:text-dark-textMuted">
          <Loader2 className="h-5 w-5 animate-spin text-accent-600" /> Memuat status analisis...
        </div>
      )}

      {error && (
        <div role="alert" className="flex items-start gap-3 rounded-md border border-semantic-error/30 bg-semantic-error/5 p-4 text-sm text-badgeText-error dark:text-badgeText-error-dark">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" /> {error}
        </div>
      )}

      {detail && status && !isLoading && (
        <div className="space-y-5">
          <section aria-labelledby="analysis-metadata-title" className="space-y-3">
            <h2 id="analysis-metadata-title" className="text-base font-semibold text-neutral-900 dark:text-dark-text">
              Analysis
            </h2>
            <dl className="grid gap-x-8 gap-y-4 border-y border-neutral-200 py-4 text-sm dark:border-dark-border sm:grid-cols-2">
              <div className="min-w-0">
                <dt className="text-xs font-medium text-neutral-500 dark:text-dark-textMuted">Analysis ID</dt>
                <dd className="mt-1 break-all font-mono text-neutral-900 dark:text-dark-text">{detail.analysis.id}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium text-neutral-500 dark:text-dark-textMuted">File name</dt>
                <dd className="mt-1 break-all font-medium text-neutral-900 dark:text-dark-text">
                  {detail.analysis.original_filename || 'Not available'}
                </dd>
              </div>
              {timestamp && (
                <div>
                  <dt className="text-xs font-medium text-neutral-500 dark:text-dark-textMuted">Created</dt>
                  <dd className="mt-1 text-neutral-900 dark:text-dark-text">
                    <time dateTime={detail.analysis.created_at || undefined}>{timestamp}</time>
                  </dd>
                </div>
              )}
              <div>
                <dt className="text-xs font-medium text-neutral-500 dark:text-dark-textMuted">Original dimensions</dt>
                <dd className="mt-1 text-neutral-900 dark:text-dark-text">
                  {detail.input.width && detail.input.height
                    ? `${detail.input.width} × ${detail.input.height} px`
                    : 'Not available'}
                </dd>
              </div>
            </dl>
          </section>

          {status === 'processing' && (
            <div role="status" className="flex items-start gap-3 border-l-4 border-accent-600 bg-accent-50 p-4 text-sm text-neutral-800 dark:bg-dark-surface dark:text-dark-text">
              <Activity className="mt-0.5 h-4 w-4 shrink-0 text-accent-700 dark:text-accent-500" />
              <p>Analysis is being processed.</p>
            </div>
          )}

          {status === 'failed' && (
            <div role="alert" className="flex items-start gap-3 border-l-4 border-semantic-error bg-semantic-error/5 p-4 text-sm text-neutral-800 dark:text-dark-text">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-semantic-error" />
              <p>{detail.analysis.error_message || 'Analysis could not be completed. Please try again.'}</p>
            </div>
          )}

          <section aria-labelledby="original-image-title" className="space-y-3">
            <h2 id="original-image-title" className="text-lg font-semibold text-neutral-900 dark:text-dark-text">Original Image</h2>
            <ImagePanel
              title={detail.analysis.original_filename || 'Original Image'}
              url={detail.input.original_image_url}
              alt={`Original image${detail.analysis.original_filename ? `: ${detail.analysis.original_filename}` : ''}`}
              unavailableMessage="Original image is not available."
              imageFailed={failedImages.original}
              onImageError={() => setFailedImages((previous) => ({ ...previous, original: true }))}
            />
          </section>

          <section aria-labelledby="segmentation-title" className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 id="segmentation-title" className="text-lg font-semibold text-neutral-900 dark:text-dark-text">Segmentation Result</h2>
              {detail.model_analysis?.detection_category === 'POLYP_DETECTED' && (
                <Badge variant="success">Polyp Detected</Badge>
              )}
              {detail.model_analysis?.detection_category === 'NO_POLYP_DETECTED' && (
                <Badge variant="info">No Polyp Detected</Badge>
              )}
              {detail.model_analysis?.detection_category === 'LOW_CONFIDENCE' && (
                <Badge variant="warning">Low Confidence</Badge>
              )}
            </div>

            {detail.model_analysis?.detection_category === 'LOW_CONFIDENCE' && (
              <div role="status" className="flex items-start gap-3 rounded-md border border-semantic-warning/30 bg-semantic-warning/10 p-3 text-xs text-badgeText-warning dark:text-semantic-warning">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                <p>
                  <strong>Perhatian:</strong> Model mendeteksi area polip dengan tingkat keyakinan rendah atau marjinal. Hasil segmentasi kurang meyakinkan dan memerlukan verifikasi serta peninjauan visual langsung oleh dokter spesialis.
                </p>
              </div>
            )}

            {detail.model_analysis?.detection_category === 'NO_POLYP_DETECTED' && (
              <div role="status" className="flex items-start gap-3 rounded-md border border-neutral-200 bg-neutral-50 p-3 text-xs text-neutral-600 dark:border-dark-border dark:bg-dark-elevated dark:text-dark-textMuted">
                <p>
                  <strong>Catatan Klinis:</strong> Tidak ada area polip yang terdeteksi oleh model pada citra ini. Ketiadaan deteksi oleh AI bukan merupakan diagnosis medis normal atau jaminan ketiadaan lesi.
                </p>
              </div>
            )}
            <div className="grid gap-4 sm:grid-cols-2">
              <ImagePanel
                title="Segmentation Mask"
                url={detail.segmentation?.binary_mask_url}
                alt="Segmentation mask"
                unavailableMessage={unavailableMessage(status, 'Segmentation output')}
                imageFailed={failedImages.mask}
                onImageError={() => setFailedImages((previous) => ({ ...previous, mask: true }))}
              />
              <ImagePanel
                title="Segmentation Overlay"
                url={detail.segmentation?.overlay_url}
                alt="Segmentation overlay"
                unavailableMessage={unavailableMessage(status, 'Segmentation output')}
                imageFailed={failedImages.segmentationOverlay}
                onImageError={() => setFailedImages((previous) => ({ ...previous, segmentationOverlay: true }))}
              />
            </div>
          </section>

          <section aria-labelledby="gradcam-title" className="space-y-3">
            <h2 id="gradcam-title" className="text-lg font-semibold text-neutral-900 dark:text-dark-text">Explainability (Grad-CAM)</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <ImagePanel
                title="Grad-CAM Heatmap"
                url={detail.gradcam?.heatmap_url}
                alt="Grad-CAM heatmap"
                unavailableMessage={unavailableMessage(status, 'Grad-CAM output')}
                imageFailed={failedImages.heatmap}
                onImageError={() => setFailedImages((previous) => ({ ...previous, heatmap: true }))}
              />
              <ImagePanel
                title="Grad-CAM Overlay"
                url={detail.gradcam?.overlay_url}
                alt="Grad-CAM overlay"
                unavailableMessage={unavailableMessage(status, 'Grad-CAM output')}
                imageFailed={failedImages.gradcamOverlay}
                onImageError={() => setFailedImages((previous) => ({ ...previous, gradcamOverlay: true }))}
              />
            </div>
          </section>

          <section aria-labelledby="model-analysis-title" className="space-y-3">
            <h2 id="model-analysis-title" className="text-lg font-semibold text-neutral-900 dark:text-dark-text">Model Analysis</h2>
            {modelDetails.length > 0 ? (
              <dl className="grid gap-x-8 gap-y-4 border-y border-neutral-200 py-4 text-sm dark:border-dark-border sm:grid-cols-2">
                {modelDetails.map(([label, value]) => (
                  <div key={label}>
                    <dt className="text-xs font-medium text-neutral-500 dark:text-dark-textMuted">{label}</dt>
                    <dd className="mt-1 text-neutral-900 dark:text-dark-text">{value}</dd>
                  </div>
                ))}
              </dl>
            ) : (
              <p className="border-y border-neutral-200 py-4 text-sm text-neutral-600 dark:border-dark-border dark:text-dark-textMuted">
                {unavailableMessage(status, 'Model analysis')}
              </p>
            )}
          </section>

          <section aria-labelledby="summary-title" className="space-y-3">
            <h2 id="summary-title" className="text-lg font-semibold text-neutral-900 dark:text-dark-text">Analysis Summary</h2>
            <p className="border-y border-neutral-200 py-4 text-sm text-neutral-700 dark:border-dark-border dark:text-dark-textMuted">
              {detail.summary?.text || unavailableMessage(status, 'Analysis summary')}
            </p>
          </section>

          <aside className="border-t border-neutral-200 pt-4 text-xs leading-relaxed text-neutral-600 dark:border-dark-border dark:text-dark-textMuted">
            <h2 className="mb-1 font-semibold text-neutral-900 dark:text-dark-text">Medical Disclaimer</h2>
            Hasil yang ditampilkan merupakan keluaran analisis model AI dan ditujukan sebagai informasi pendukung bagi tenaga medis. Hasil ini tidak dimaksudkan sebagai diagnosis medis atau pengganti penilaian profesional tenaga medis.
          </aside>
        </div>
      )}
    </div>
  );
};

export default AnalysisResult;
