import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { LoadingState } from '@/components/ui/LoadingState';
import { Modal } from '@/components/ui/Modal';
import { PlusCircle, ArrowLeft, ArrowRight, Eye, Calendar, FileText, Trash2 } from 'lucide-react';
import { deleteAnalysis, listHistory, type HistoryItem } from '@/services/analysis';

function formatDate(value: string | null): string {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString('id-ID', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function statusBadge(item: HistoryItem): { variant: 'success' | 'default'; label: string } {
  if (item.status === 'failed') return { variant: 'default', label: 'Gagal' };
  if (item.status === 'processing') return { variant: 'default', label: 'Diproses' };
  if (item.segmentation_status === 'detected') return { variant: 'success', label: 'Terdeteksi' };
  if (item.segmentation_status === 'not_detected') return { variant: 'default', label: 'Tidak Terdeteksi' };
  return { variant: 'default', label: 'Selesai' };
}

export const History: React.FC = () => {
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<HistoryItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const loadHistory = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const result = await listHistory();
      setItems(result.items ?? []);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Gagal memuat riwayat pemeriksaan.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  const confirmDelete = useCallback(async () => {
    if (!pendingDelete || isDeleting) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteAnalysis(pendingDelete.id);
      setItems((current) => current.filter((item) => item.id !== pendingDelete.id));
      setPendingDelete(null);
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : 'Gagal menghapus riwayat pemeriksaan.');
    } finally {
      setIsDeleting(false);
    }
  }, [pendingDelete, isDeleting]);

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200 dark:border-dark-border pb-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link to="/dashboard" className="text-xs text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 inline-flex items-center gap-1">
              <ArrowLeft className="w-3.5 h-3.5" /> Dashboard
            </Link>
            <span className="text-neutral-300 dark:text-neutral-700">/</span>
            <Badge variant="accent">Riwayat</Badge>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-neutral-900 dark:text-dark-text">
            Riwayat Pemeriksaan
          </h1>
          <p className="text-sm text-neutral-600 dark:text-dark-textMuted leading-relaxed">
            Daftar seluruh sesi analisis citra polip kolonoskopi yang tersimpan dalam sistem.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link to="/analysis/new">
            <Button variant="primary" size="md" leftIcon={<PlusCircle className="w-4 h-4" />}>
              Analisis Baru
            </Button>
          </Link>
        </div>
      </div>

      {isLoading ? (
        <LoadingState
          title="Memuat riwayat pemeriksaan"
          description="Mengambil daftar sesi analisis milik Anda dari server."
        />
      ) : loadError ? (
        <ErrorState
          code="HISTORY_LOAD_FAILED"
          message={loadError}
          onRetry={() => void loadHistory()}
        />
      ) : items.length === 0 ? (
        <EmptyState
          title="Belum ada riwayat pemeriksaan"
          description="Hasil analisis yang Anda simpan akan tampil di sini."
          action={
            <Link to="/analysis/new">
              <Button variant="primary" size="sm" leftIcon={<PlusCircle className="w-4 h-4" />}>
                Mulai Analisis Baru
              </Button>
            </Link>
          }
        />
      ) : (
        <Card className="divide-y divide-neutral-200 dark:divide-dark-border">
          <div className="p-4 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-neutral-50/50 dark:bg-dark-elevated/30">
            <div>
              <h2 className="text-base font-semibold text-neutral-900 dark:text-dark-text">
                Daftar Arsip Analisis
              </h2>
              <p className="text-xs text-neutral-600 dark:text-dark-textMuted">
                {items.length} sesi pemeriksaan tersimpan
              </p>
            </div>
            <Badge variant="default">{items.length} sesi</Badge>
          </div>

          {items.map((item) => {
            const badge = statusBadge(item);
            return (
              <div
                key={item.id}
                className="p-4 sm:p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-neutral-50 dark:hover:bg-dark-elevated transition-colors"
              >
                <div className="flex items-start gap-4">
                  {item.thumbnail_url ? (
                    <img
                      src={item.thumbnail_url}
                      alt={item.original_filename ?? 'Citra pemeriksaan'}
                      className="w-12 h-12 rounded-md object-cover flex-shrink-0 border border-neutral-200 dark:border-dark-border"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-md bg-neutral-100 dark:bg-dark-elevated flex items-center justify-center text-neutral-700 dark:text-neutral-300 flex-shrink-0">
                      <FileText className="w-6 h-6" />
                    </div>
                  )}
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-neutral-900 dark:text-dark-text">
                        {item.original_filename ?? 'Sesi Pemeriksaan'}
                      </span>
                      <Badge variant={badge.variant}>{badge.label}</Badge>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-neutral-500 dark:text-dark-textMuted">
                      <span className="flex items-center gap-1 font-mono">
                        ID: {item.id}
                      </span>
                      <span>&bull;</span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5" /> {formatDate(item.created_at)}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center">
                  <Link to={`/history/${item.id}`}>
                    <Button variant="outline" size="sm" leftIcon={<Eye className="w-3.5 h-3.5" />}>
                      Detail Riwayat
                    </Button>
                  </Link>
                  <Link to={`/analysis/${item.id}`}>
                    <Button variant="secondary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                      Lihat Visualisasi
                    </Button>
                  </Link>
                  <Button
                    variant="danger"
                    size="sm"
                    leftIcon={<Trash2 className="w-3.5 h-3.5" />}
                    onClick={() => {
                      setDeleteError(null);
                      setPendingDelete(item);
                    }}
                    aria-label={`Hapus ${item.original_filename ?? item.id}`}
                  >
                    Hapus
                  </Button>
                </div>
              </div>
            );
          })}
        </Card>
      )}

      <Modal
        isOpen={pendingDelete !== null}
        onClose={() => {
          if (!isDeleting) {
            setPendingDelete(null);
            setDeleteError(null);
          }
        }}
        title="Hapus riwayat pemeriksaan?"
        description="Tindakan ini akan menghapus hasil analisis beserta seluruh citra tersimpan dan tidak dapat dibatalkan."
      >
        <div className="space-y-4">
          <p className="text-xs text-neutral-600 dark:text-dark-textMuted">
            Sesi yang akan dihapus:{' '}
            <span className="font-mono font-semibold text-neutral-900 dark:text-dark-text">
              {pendingDelete?.original_filename ?? pendingDelete?.id}
            </span>
          </p>
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
                setPendingDelete(null);
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

export default History;
