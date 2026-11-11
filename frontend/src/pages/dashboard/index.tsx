import React, { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { LoadingState } from '@/components/ui/LoadingState';
import { listHistory, type HistoryItem } from '@/utils/analysis';
import { formatAnalysisDate } from '@/utils/format';
import {
  Plus,
  PlusCircle,
  ArrowRight,
  Calendar,
  CheckCircle2,
  Loader2,
  AlertCircle,
  ImageOff,
  FileText,
} from 'lucide-react';

/** Jumlah kartu terbaru yang ditampilkan (mengikuti referensi: 4 kartu). */
const LATEST_ANALYSIS_LIMIT = 4;

interface StatusPresentation {
  badgeVariant: 'success' | 'accent' | 'error';
  badgeIcon: React.ReactNode;
  badgeLabel: string;
}

/**
 * Label status memakai Bahasa Indonesia agar konsisten dengan halaman
 * Riwayat yang sudah ada (keputusan Phase 1). Warna/ikon mengikuti
 * StyleGuide §31: status tidak dibedakan lewat warna saja.
 */
function statusPresentation(status: HistoryItem['status']): StatusPresentation {
  if (status === 'failed') {
    return {
      badgeVariant: 'error',
      badgeIcon: <AlertCircle className="w-3 h-3" aria-hidden="true" />,
      badgeLabel: 'Failed',
    };
  }
  if (status === 'processing') {
    return {
      badgeVariant: 'accent',
      badgeIcon: <Loader2 className="w-3 h-3" aria-hidden="true" />,
      badgeLabel: 'Processing',
    };
  }
  return {
    badgeVariant: 'success',
    badgeIcon: <CheckCircle2 className="w-3 h-3" aria-hidden="true" />,
    badgeLabel: 'Completed',
  };
}

/**
 * Area gambar kartu. Citra medis contoh dari screenshot TIDAK disalin ke
 * aset produksi: hanya `thumbnail_url` nyata dari API yang ditampilkan.
 * Jika tidak ada, dipakai placeholder netral sesuai status.
 */
const CardThumbnail: React.FC<{ item: HistoryItem }> = ({ item }) => {
  if (item.status === 'processing') {
    return (
      <div className="flex h-full w-full items-center justify-center" aria-hidden="true">
        <Loader2 className="w-8 h-8 animate-spin text-accent-600 dark:text-accent-500" />
      </div>
    );
  }

  if (item.status === 'failed') {
    return (
      <div className="flex h-full w-full items-center justify-center" aria-hidden="true">
        <ImageOff className="w-8 h-8 text-semantic-error" />
      </div>
    );
  }

  if (item.thumbnail_url) {
    return (
      <img
        src={item.thumbnail_url}
        alt={item.original_filename ?? 'Examination image'}
        className="h-full w-full object-cover"
        loading="lazy"
      />
    );
  }

  return (
    <div className="flex h-full w-full items-center justify-center text-neutral-400 dark:text-neutral-500" aria-hidden="true">
      <FileText className="w-8 h-8" />
    </div>
  );
};

/** Aksi kanan-bawah kartu, mengikuti status analisis. */
const CardAction: React.FC<{ item: HistoryItem }> = ({ item }) => {
  if (item.status === 'processing') {
    return (
      <span className="text-xs text-neutral-500 dark:text-neutral-400">In progress</span>
    );
  }

  if (item.status === 'failed') {
    return (
      <Link
        to="/analysis/new"
        className="inline-flex items-center gap-1 text-xs font-medium text-badgeText-error dark:text-badgeText-error-dark hover:underline"
      >
        Try Again
      </Link>
    );
  }

  return (
    <Link
      to={`/analysis/${item.id}`}
      className="inline-flex items-center gap-1 text-xs font-medium text-accent-600 hover:underline dark:text-accent-500"
    >
      View Result
      <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
    </Link>
  );
};

const AnalysisCard: React.FC<{ item: HistoryItem }> = ({ item }) => {
  const status = statusPresentation(item.status);

  return (
    <article className="flex flex-col overflow-hidden rounded-lg border border-neutral-200 bg-white shadow-sm transition-colors dark:border-dark-border dark:bg-dark-surface">
      <div className="relative h-40 w-full bg-neutral-100 dark:bg-dark-bg">
        <CardThumbnail item={item} />
      </div>

      {/* Padding horizontal 16px agar divider berjarak tepat 16px dari tepi
          kartu (seperti referensi); padding atas lebih besar agar tinggi
          panel mendekati referensi (~126px). */}
      <div className="flex flex-1 flex-col px-4 pt-5 pb-4">
        <p className="truncate text-sm font-medium text-neutral-900 dark:text-dark-text">
          {item.original_filename ?? 'Examination Session'}
        </p>

        <p className="mt-3 flex items-center gap-1.5 text-xs text-neutral-500 dark:text-dark-textMuted">
          <Calendar className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          {formatAnalysisDate(item.created_at)}
        </p>

        <div className="mt-auto flex items-center justify-between gap-2 border-t border-neutral-100 pt-3 dark:border-dark-border">
          <Badge
            variant={status.badgeVariant}
            size="sm"
            uppercase={false}
            icon={status.badgeIcon}
          >
            {status.badgeLabel}
          </Badge>
          <CardAction item={item} />
        </div>
      </div>
    </article>
  );
};

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const loadLatest = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const result = await listHistory();
      // Hanya data nyata dari API, dibatasi 4 terbaru — tidak ada rekayasa record.
      setItems(result.items.slice(0, LATEST_ANALYSIS_LIMIT));
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : 'Failed to load latest analyses.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadLatest();
  }, [loadLatest]);

  return (
    <div className="space-y-6">
      {/* Page context */}
      <div className="space-y-3">
        <h1 className="text-3xl font-bold tracking-tight text-neutral-900 dark:text-dark-text">
          Dashboard
        </h1>
        {/* Lebar & ukuran teks mengikuti referensi (paragraf membungkus pada
            "…segmentation"). */}
        <p className="max-w-xl text-base leading-normal text-neutral-600 dark:text-dark-textMuted">
          Welcome back. Use PIXEL-T to perform endoscopic image segmentation analysis and view
          Grad-CAM visualizations.
        </p>
      </div>

      {/* Primary CTA. Padding vertikal mengikuti referensi (panel 115px). */}
      <section className="flex flex-col gap-4 rounded-lg border border-neutral-200 bg-white p-7 sm:flex-row sm:items-center sm:justify-between dark:border-dark-border dark:bg-dark-surface">
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-dark-text">
            Start New Analysis
          </h2>
          <p className="text-sm text-neutral-600 dark:text-dark-textMuted">
            Upload an endoscopic image to obtain segmentation results and Grad-CAM visualization.
          </p>
        </div>
        {/* Primary CTA — KEPUTUSAN PENGGUNA: StyleGuide-first. §29 mewajibkan
            "Gunakan Deep Medical Navy" untuk action utama "New Analysis", jadi
            tombol ini memakai primary-900 (#0F3D56) sesuai §5.1.
            - rest  primary-900 #0F3D56
            - hover primary-700 #1C5B76 (lebih terang → afordans hover jelas)
            - press primary-800 #164B65 (token §5.1 "Hover / active"; lebih
              gelap dari hover sehingga keadaan tekan terasa "tenggelam", dan
              tetap berbeda dari keadaan diam)
            Ketiganya token palet primary yang valid, sehingga `accent-800`
            (yang memang tidak ada pada skala accent) tidak lagi dipakai.
            Teks putih dipertahankan; pasangan fg/bg ini lolos WCAG AAA
            (11.53:1 rest, 7.48:1 hover, 9.42:1 press).
            DIVERGENSI YANG DISETUJUI: referensi Dashboard memakai tombol teal
            #18A6A6 (accent-600). Mengikuti §29, tombol ini kini Navy —
            penyimpangan visual yang dilaporkan, bukan salah implementasi. */}
        <Link
          to="/analysis/new"
          className="inline-flex shrink-0 items-center justify-center gap-2 rounded-md bg-primary-900 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-700 active:bg-primary-800 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-dark-bg"
        >
          <Plus className="w-4 h-4" aria-hidden="true" />
          <span>New Analysis</span>
        </Link>
      </section>

      {/* Recent analyses */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-neutral-900 dark:text-dark-text">
            Latest Analysis
          </h2>
          <Link
            to="/history"
            className="inline-flex items-center gap-1 text-xs font-medium text-accent-600 hover:underline dark:text-accent-500"
          >
            See All
            <ArrowRight className="w-3 h-3" aria-hidden="true" />
          </Link>
        </div>

        {isLoading ? (
          <Card className="p-8">
            <LoadingState
              title="Loading latest analyses"
              description="Fetching your latest analysis sessions from the server."
            />
          </Card>
        ) : loadError ? (
          <ErrorState
            code="DASHBOARD_LOAD_FAILED"
            message={loadError}
            onRetry={() => void loadLatest()}
          />
        ) : items.length === 0 ? (
          <EmptyState
            title="No recent analyses yet"
            description="Start a new analysis by uploading an endoscopic image on the New Analysis page."
            action={
              /* P-06: tombol biasa + navigasi programatik (pola A11Y-03) —
                  tanpa <Link> yang membungkus <Button>. Label diubah ke Inggris. */
              <Button
                variant="primary"
                size="sm"
                leftIcon={<PlusCircle className="w-4 h-4" />}
                onClick={() => navigate('/analysis/new')}
              >
                Start New Analysis
              </Button>
            }
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {items.map((item) => (
              <AnalysisCard key={item.id} item={item} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
};

export default Dashboard;
