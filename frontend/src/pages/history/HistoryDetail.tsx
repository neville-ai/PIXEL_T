import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Modal } from '@/components/ui/Modal';
import { ArrowLeft, ArrowRight, Trash2 } from 'lucide-react';
import { deleteAnalysis, getAnalysis, type AnalysisDetail } from '@/services/analysis';

function segmentationLabel(detail: AnalysisDetail | null): string {
  if (!detail) return '-';
  if (detail.analysis.status === 'failed') return 'Gagal';
  if (detail.analysis.status === 'processing') return 'Diproses';
  if (detail.model_analysis?.segmentation_status === 'detected') return 'Terdeteksi';
  if (detail.model_analysis?.segmentation_status === 'not_detected') return 'Tidak Terdeteksi';
  return 'Selesai';
}

export const HistoryDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<AnalysisDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const loadDetail = useCallback(async () => {
    if (!id) {
      setLoadError('Identifier riwayat tidak ditentukan.');
      setIsLoading(false);
      return;
    }
    setIsLoading(true);
    setLoadError(null);
    try {
      setDetail(await getAnalysis(id));
    } catch (err) {
      setDetail(null);
      setLoadError(err instanceof Error ? err.message : 'Gagal memuat detail riwayat.');
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadDetail();
  }, [loadDetail]);

  const confirmDelete = useCallback(async () => {
    if (!id || isDeleting) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteAnalysis(id);
      navigate('/history');
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Gagal menghapus riwayat pemeriksaan.');
    } finally {
      setIsDeleting(false);
    }
  }, [id, isDeleting, navigate]);

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200 dark:border-dark-border pb-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link to="/dashboard" className="text-xs text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 inline-flex items-center gap-1">
              <ArrowLeft className="w-3.5 h-3.5" /> Dashboard
            </Link>
            <span className="text-neutral-300 dark:text-neutral-700">/</span>
            <Link to="/history" className="text-xs text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200">
              Riwayat
            </Link>
            <span className="text-neutral-300 dark:text-neutral-700">/</span>
            <Badge variant="accent">Detail Arsip</Badge>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-neutral-900 dark:text-dark-text">
              Detail Arsip Pemeriksaan
            </h1>
            <Badge variant="default" className="font-mono text-xs">
              ID: {id || 'Tidak ditentukan'}
            </Badge>
          </div>
          <p className="text-sm text-neutral-600 dark:text-dark-textMuted leading-relaxed">
            Informasi riwayat metadata dan tautan akses ke visualisasi segmentasi dan Grad-CAM.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <Link to="/history">
            <Button variant="outline" size="sm" leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Kembali ke Riwayat
            </Button>
          </Link>
          <Link to={`/analysis/${id}`}>
            <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
              Buka Hasil Analisis
            </Button>
          </Link>
          <Button
            variant="danger"
            size="sm"
            leftIcon={<Trash2 className="w-4 h-4" />}
            onClick={() => {
              setDeleteError(null);
              setIsConfirmOpen(true);
            }}
            disabled={isLoading || detail === null}
          >
            Hapus
          </Button>
        </div>
      </div>

      {isLoading ? (
        <LoadingState
          title="Memuat detail riwayat"
          description="Mengambil metadata sesi analisis dari server."
        />
      ) : loadError || !detail ? (
        <ErrorState
          code="HISTORY_DETAIL_FAILED"
          message={loadError ?? 'Detail riwayat tidak tersedia.'}
          onRetry={() => void loadDetail()}
        />
      ) : (
        <Card className="p-6 space-y-6">
          <CardHeader className="p-0">
            <CardTitle className="text-lg">Metadata Pemeriksaan</CardTitle>
            <CardDescription>Rincian log catatan analisis klinis</CardDescription>
          </CardHeader>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-md bg-neutral-50 dark:bg-dark-elevated border border-neutral-200 dark:border-dark-border space-y-1">
              <span className="text-neutral-500 dark:text-dark-textMuted font-medium">Identifier Riwayat</span>
              <p className="font-mono text-sm font-semibold text-neutral-900 dark:text-dark-text">{detail.analysis.id}</p>
            </div>
            <div className="p-4 rounded-md bg-neutral-50 dark:bg-dark-elevated border border-neutral-200 dark:border-dark-border space-y-1">
              <span className="text-neutral-500 dark:text-dark-textMuted font-medium">Status Segmentasi</span>
              <div>
                <Badge variant="default">{segmentationLabel(detail)}</Badge>
              </div>
            </div>
            <div className="p-4 rounded-md bg-neutral-50 dark:bg-dark-elevated border border-neutral-200 dark:border-dark-border space-y-1">
              <span className="text-neutral-500 dark:text-dark-textMuted font-medium">Nama Berkas</span>
              <p className="text-neutral-800 dark:text-dark-text font-semibold">{detail.analysis.original_filename ?? '-'}</p>
            </div>
            <div className="p-4 rounded-md bg-neutral-50 dark:bg-dark-elevated border border-neutral-200 dark:border-dark-border space-y-1">
              <span className="text-neutral-500 dark:text-dark-textMuted font-medium">Kerangka Kerja Model</span>
              <p className="text-neutral-800 dark:text-dark-text font-semibold">
                {detail.model?.architecture ?? 'U-Net'} ({detail.model?.version ?? 'Scenario 1 Ver.22'})
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-neutral-100 dark:border-dark-border flex flex-col sm:flex-row items-center justify-between gap-3">
            <span className="text-xs text-neutral-500 dark:text-dark-textMuted">
              Akses langsung visualisasi segmentasi untuk ID ini:
            </span>
            <Link to={`/analysis/${id}`}>
              <Button variant="accent" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Buka /analysis/{id}
              </Button>
            </Link>
          </div>
        </Card>
      )}

      <Modal
        isOpen={isConfirmOpen}
        onClose={() => {
          if (!isDeleting) {
            setIsConfirmOpen(false);
            setDeleteError(null);
          }
        }}
        title="Hapus riwayat pemeriksaan?"
        description="Tindakan ini akan menghapus hasil analisis beserta seluruh citra tersimpan dan tidak dapat dibatalkan."
      >
        <div className="space-y-4">
          {deleteError && (
            <div role="alert" className="p-3 rounded-md border border-semantic-error/30 bg-semantic-error/5 text-xs text-neutral-700 dark:text-neutral-300">
              {deleteError}
            </div>
          )}
          <div className="flex items-center justify-end gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setIsConfirmOpen(false);
                setDeleteError(null);
              }}
              disabled={isDeleting}
            >
              Batal
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => void confirmDelete()}
              isLoading={isDeleting}
              leftIcon={<Trash2 className="w-3.5 h-3.5" />}
            >
              Ya, Hapus
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default HistoryDetail;
