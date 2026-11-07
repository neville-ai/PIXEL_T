import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { LoadingState } from '@/components/ui/LoadingState';
import { Modal } from '@/components/ui/Modal';
import {
  PlusCircle,
  ArrowLeft,
  Eye,
  FileText,
  Trash2,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  AlertTriangle,
  Circle,
} from 'lucide-react';
import { deleteAnalysis, listHistory, type HistoryItem } from '@/services/analysis';
import { formatAnalysisDate } from '@/lib/format';

/** Item per halaman — mengikuti referensi yang menampilkan 4 baris. */
const PAGE_SIZE = 4;

type StatusFilter = 'all' | 'processing' | 'completed' | 'failed';

interface StatusBadgeSpec {
  variant: 'success' | 'default' | 'error';
  label: string;
  icon: React.ReactNode;
}

/**
 * Label status sengaja memakai "COMPLETED" (bukan "COOMPLETED" seperti pada
 * render referensi) dan "FAILED" — keduanya merupakan nilai `status` asli dari
 * API (APIContract §20.1). Tidak ada label yang dikarang.
 */
function statusBadge(status: HistoryItem['status']): StatusBadgeSpec {
  if (status === 'completed') {
    return { variant: 'success', label: 'COMPLETED', icon: <CheckCircle2 className="w-3 h-3" /> };
  }
  if (status === 'processing') {
    return { variant: 'default', label: 'PROCESSING', icon: <Circle className="w-3 h-3" /> };
  }
  return { variant: 'error', label: 'FAILED', icon: <AlertTriangle className="w-3 h-3" /> };
}

/** `YYYY-MM-DD` dari tanggal lokal, dipakai pencocokan filter tanggal. */
function toDateKey(date: Date): string {
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  return `${date.getFullYear()}-${month}-${day}`;
}

/** "2 Okt 2026, 14:20" -> baris tanggal + baris jam (dipakai kolom tabel). */
function splitAnalysisDate(value: string | null): { day: string; time: string } {
  const formatted = formatAnalysisDate(value);
  const separator = formatted.indexOf(', ');
  if (separator === -1) return { day: formatted, time: '' };
  return { day: formatted.slice(0, separator), time: formatted.slice(separator + 2) };
}

export const History: React.FC = () => {
  const navigate = useNavigate();
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [pendingDelete, setPendingDelete] = useState<HistoryItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [dateFilter, setDateFilter] = useState('');
  const [page, setPage] = useState(1);

  const loadHistory = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    try {
      const result = await listHistory();
      setItems(result.items ?? []);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Failed to load your analysis history.');
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
      setDeleteError(err instanceof Error ? err.message : 'Failed to delete this history session.');
    } finally {
      setIsDeleting(false);
    }
  }, [pendingDelete, isDeleting]);

  /**
   * Filter berjalan di atas data yang sudah dimuat (API daftar riwayat tidak
   * menerima parameter filter/pagination, APIContract §20.1).
   */
  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return items.filter((item) => {
      if (statusFilter !== 'all' && item.status !== statusFilter) return false;
      if (dateFilter) {
        if (!item.created_at) return false;
        const created = new Date(item.created_at);
        if (Number.isNaN(created.getTime())) return false;
        if (toDateKey(created) !== dateFilter) return false;
      }
      if (needle) {
        const filename = (item.original_filename ?? '').toLowerCase();
        if (!filename.includes(needle)) return false;
      }
      return true;
    });
  }, [items, query, statusFilter, dateFilter]);

  const hasActiveFilters = query.trim() !== '' || statusFilter !== 'all' || dateFilter !== '';

  const resetFilters = useCallback(() => {
    setQuery('');
    setStatusFilter('all');
    setDateFilter('');
    setPage(1);
  }, []);

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, pageCount);
  const pageStart = (currentPage - 1) * PAGE_SIZE;
  const pageItems = filtered.slice(pageStart, pageStart + PAGE_SIZE);

  const rangeStart = filtered.length === 0 ? 0 : pageStart + 1;
  const rangeEnd = pageStart + pageItems.length;
  // Satu string utuh agar jumlah yang dimuat terbaca sebagai satu blok teks.
  const summary = `Showing ${rangeStart}–${rangeEnd} of ${filtered.length} matching of ${items.length} loaded`;

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-neutral-200 dark:border-dark-border pb-6">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link
              to="/dashboard"
              className="text-xs text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200 inline-flex items-center gap-1"
            >
              <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
            </Link>
            <span className="text-neutral-300 dark:text-neutral-700">/</span>
            <span className="text-xs font-medium text-neutral-700 dark:text-neutral-300">
              Analysis History
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-neutral-900 dark:text-dark-text">
            Analysis History
          </h1>
          <p className="text-sm text-neutral-600 dark:text-dark-textMuted leading-relaxed">
            Find, review, and manage your colonoscopy imaging examination archives.
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* P-06: tombol biasa + navigasi programatik (pola A11Y-03) — tanpa
              <Link> yang membungkus <Button> (elemen interaktif bersarang). */}
          <Button
            variant="accent"
            size="md"
            leftIcon={<PlusCircle className="w-4 h-4" />}
            onClick={() => navigate('/analysis/new')}
          >
            New Analysis
          </Button>
        </div>
      </div>

      {isLoading ? (
        <LoadingState
          title="Loading analysis history"
          description="Fetching your saved analysis sessions from the server."
        />
      ) : loadError ? (
        <ErrorState
          code="HISTORY_LOAD_FAILED"
          message={loadError}
          onRetry={() => void loadHistory()}
        />
      ) : items.length === 0 ? (
        <EmptyState
          title="No analysis history yet"
          description="Your saved analysis results will appear here."
          action={
            <Button
              variant="accent"
              size="sm"
              leftIcon={<PlusCircle className="w-4 h-4" />}
              onClick={() => navigate('/analysis/new')}
            >
              Start New Analysis
            </Button>
          }
        />
      ) : (
        <Card className="space-y-6">
          {/* Toolbar filter */}
          <div className="flex flex-col lg:flex-row lg:items-end gap-3">
            <div className="flex-1 min-w-0">
              <label
                htmlFor="history-search"
                className="block text-xs font-semibold uppercase tracking-wider text-neutral-700 dark:text-neutral-300 mb-1.5"
              >
                Search by file name
              </label>
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400 dark:text-neutral-500" />
                <input
                  id="history-search"
                  type="search"
                  value={query}
                  onChange={(event) => {
                    setQuery(event.target.value);
                    setPage(1);
                  }}
                  placeholder="Search by image file name (e.g., case_colonoscopy_043.png)"
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-md border border-neutral-300 dark:border-dark-border bg-white dark:bg-dark-surface text-neutral-900 dark:text-dark-text placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-700"
                />
              </div>
            </div>

            <div className="lg:w-56">
              <label
                htmlFor="history-status"
                className="block text-xs font-semibold uppercase tracking-wider text-neutral-700 dark:text-neutral-300 mb-1.5"
              >
                Status
              </label>
              <select
                id="history-status"
                value={statusFilter}
                onChange={(event) => {
                  setStatusFilter(event.target.value as StatusFilter);
                  setPage(1);
                }}
                className="w-full px-3 py-2 text-sm rounded-md border border-neutral-300 dark:border-dark-border bg-white dark:bg-dark-surface text-neutral-900 dark:text-dark-text focus:outline-none focus:ring-2 focus:ring-primary-700"
              >
                <option value="all">ALL STATUSES</option>
                <option value="completed">COMPLETED</option>
                <option value="processing">PROCESSING</option>
                <option value="failed">FAILED</option>
              </select>
            </div>

            <div className="lg:w-56">
              <label
                htmlFor="history-date"
                className="block text-xs font-semibold uppercase tracking-wider text-neutral-700 dark:text-neutral-300 mb-1.5"
              >
                Analysis date
              </label>
              <input
                id="history-date"
                type="date"
                value={dateFilter}
                onChange={(event) => {
                  setDateFilter(event.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 text-sm rounded-md border border-neutral-300 dark:border-dark-border bg-white dark:bg-dark-surface text-neutral-900 dark:text-dark-text focus:outline-none focus:ring-2 focus:ring-primary-700"
              />
            </div>

            <Button
              variant="outline"
              size="md"
              leftIcon={<Filter className="w-4 h-4" />}
              onClick={resetFilters}
              disabled={!hasActiveFilters}
            >
              RESET FILTER
            </Button>
          </div>

          {filtered.length === 0 ? (
            /* H-03: riwayat API ada, tetapi pencarian/filter tidak cocok —
               sengaja dibedakan dari EmptyState "No analysis history yet"
               (cabang items.length === 0 di atas). Aksi membersihkan query,
               filter, dan halaman sehingga semua riwayat termuat tampil lagi. */
            <div className="border border-dashed border-neutral-300 dark:border-dark-border rounded-md px-6 py-10 text-center space-y-3">
              <p className="text-sm font-semibold text-neutral-700 dark:text-neutral-300">
                No matching analyses found.
              </p>
              <p className="text-xs text-neutral-500 dark:text-neutral-400">
                Clear the search and filters to see all {items.length} loaded analyses.
              </p>
              <Button
                variant="outline"
                size="sm"
                leftIcon={<Filter className="w-4 h-4" />}
                onClick={resetFilters}
              >
                CLEAR FILTERS
              </Button>
            </div>
          ) : (
            <>
          {/* Tabel desktop */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-neutral-200 dark:border-dark-border">
                  <th className="py-3 pr-4 text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                    Image &amp; File Name
                  </th>
                  <th className="py-3 pr-4 text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                    Date of Analysis
                  </th>
                  <th className="py-3 pr-4 text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                    Inference Status
                  </th>
                  <th className="py-3 text-right text-xs font-semibold uppercase tracking-wider text-neutral-500 dark:text-neutral-400">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-200 dark:divide-dark-border">
                {pageItems.map((item) => {
                  const badge = statusBadge(item.status);
                  const date = splitAnalysisDate(item.created_at);
                  const isCompleted = item.status === 'completed';
                  const isFailed = item.status === 'failed';
                  return (
                    <tr
                      key={item.id}
                      className="hover:bg-neutral-50 dark:hover:bg-dark-elevated transition-colors"
                    >
                      <td className="py-3 pr-4 align-middle">
                        <div className="flex items-center gap-3 min-w-0">
                          {item.thumbnail_url ? (
                            <img
                              src={item.thumbnail_url}
                              alt={item.original_filename ?? 'Analysis thumbnail'}
                              className="w-11 h-11 rounded-md object-cover flex-shrink-0 border border-neutral-200 dark:border-dark-border"
                            />
                          ) : (
                            <div className="w-11 h-11 rounded-md bg-neutral-100 dark:bg-dark-elevated flex items-center justify-center text-neutral-500 dark:text-neutral-400 flex-shrink-0">
                              <FileText className="w-5 h-5" />
                            </div>
                          )}
                          <div className="min-w-0">
                            <div className="text-sm font-semibold text-neutral-900 dark:text-dark-text truncate max-w-[16rem]">
                              {item.original_filename ?? 'Untitled session'}
                            </div>
                            <div className="text-xs font-mono text-neutral-500 dark:text-neutral-400 truncate max-w-[16rem]">
                              ID: {item.id}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 pr-4 align-middle">
                        <div className="text-sm text-neutral-900 dark:text-dark-text whitespace-nowrap">
                          {date.day}
                        </div>
                        {date.time && (
                          <div className="text-xs text-neutral-500 dark:text-neutral-400 whitespace-nowrap">
                            {date.time}
                          </div>
                        )}
                      </td>
                      <td className="py-3 pr-4 align-middle">
                        <Badge variant={badge.variant} icon={badge.icon}>
                          {badge.label}
                        </Badge>
                      </td>
                      <td className="py-3 align-middle">
                        {/* P-06: aksi baris kini <Button> biasa + navigate()
                            — tanpa <Link> bersarang; label & tujuan tetap. */}
                        <div className="flex items-center justify-end gap-2">
                          {isCompleted || isFailed ? (
                            <Button
                              variant={isCompleted ? 'outline' : 'secondary'}
                              size="sm"
                              leftIcon={<Eye className="w-3.5 h-3.5" />}
                              onClick={() => navigate(`/analysis/${item.id}`, { state: { from: 'history' } })}
                            >
                              {isCompleted ? 'SEE RESULT' : 'DETAIL LOG'}
                            </Button>
                          ) : (
                            <Button variant="secondary" size="sm" disabled>
                              PROCESSING
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            leftIcon={<Trash2 className="w-4 h-4" />}
                            onClick={() => {
                              setDeleteError(null);
                              setPendingDelete(item);
                            }}
                            aria-label={`Delete ${item.original_filename ?? item.id}`}
                          >
                            <span className="sr-only">Delete</span>
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Kartu responsif (layar sempit) */}
          <div className="md:hidden space-y-3">
            {pageItems.map((item) => {
              const badge = statusBadge(item.status);
              const date = splitAnalysisDate(item.created_at);
              const isCompleted = item.status === 'completed';
              const isFailed = item.status === 'failed';
              return (
                <div
                  key={item.id}
                  className="rounded-lg border border-neutral-200 dark:border-dark-border p-4 space-y-3"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    {item.thumbnail_url ? (
                      <img
                        src={item.thumbnail_url}
                        alt={item.original_filename ?? 'Analysis thumbnail'}
                        className="w-11 h-11 rounded-md object-cover flex-shrink-0 border border-neutral-200 dark:border-dark-border"
                      />
                    ) : (
                      <div className="w-11 h-11 rounded-md bg-neutral-100 dark:bg-dark-elevated flex items-center justify-center text-neutral-500 dark:text-neutral-400 flex-shrink-0">
                        <FileText className="w-5 h-5" />
                      </div>
                    )}
                    <div className="min-w-0">
                      <div className="text-sm font-semibold text-neutral-900 dark:text-dark-text truncate">
                        {item.original_filename ?? 'Untitled session'}
                      </div>
                      <div className="text-xs font-mono text-neutral-500 dark:text-neutral-400 truncate">
                        ID: {item.id}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between gap-2">
                    <div className="text-xs text-neutral-500 dark:text-neutral-400">
                      {date.day}
                      {date.time && <span className="ml-1">&bull; {date.time}</span>}
                    </div>
                    <Badge variant={badge.variant} icon={badge.icon}>
                      {badge.label}
                    </Badge>
                  </div>

                  <div className="flex items-center justify-end gap-2">
                    {isCompleted || isFailed ? (
                      <Button
                        variant={isCompleted ? 'outline' : 'secondary'}
                        size="sm"
                        leftIcon={<Eye className="w-3.5 w-3.5" />}
                        onClick={() => navigate(`/analysis/${item.id}`, { state: { from: 'history' } })}
                      >
                        {isCompleted ? 'SEE RESULT' : 'DETAIL LOG'}
                      </Button>
                    ) : (
                      <Button variant="secondary" size="sm" disabled>
                        PROCESSING
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      leftIcon={<Trash2 className="w-4 h-4" />}
                      onClick={() => {
                        setDeleteError(null);
                        setPendingDelete(item);
                      }}
                      aria-label={`Delete ${item.original_filename ?? item.id}`}
                    >
                      <span className="sr-only">Delete</span>
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
            </>
          )}

          {/* Footer: ringkasan + pagination client-side */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-t border-neutral-200 dark:border-dark-border pt-4">
            <p className="text-xs font-mono text-neutral-600 dark:text-neutral-400">
              {summary}
            </p>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                leftIcon={<ChevronLeft className="w-3.5 h-3.5" />}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                disabled={currentPage <= 1}
              >
                PREV
              </Button>
              {/* Pagination client-side: hanya tombol halaman aktif yang
                  memegang aria-current="page"; pada satu halaman pun penanda
                  tetap tunggal (nilai currentPage unik di antara tombol). */}
              {Array.from({ length: pageCount }, (_, index) => index + 1).map((value) => (
                <Button
                  key={value}
                  variant={value === currentPage ? 'accent' : 'outline'}
                  size="sm"
                  aria-current={value === currentPage ? 'page' : undefined}
                  onClick={() => setPage(value)}
                >
                  {value}
                </Button>
              ))}
              <Button
                variant="outline"
                size="sm"
                rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
                onClick={() => setPage((current) => Math.min(pageCount, current + 1))}
                disabled={currentPage >= pageCount}
              >
                NEXT
              </Button>
            </div>
          </div>
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
        title="Delete this analysis session?"
        description="This permanently removes the saved analysis and its images. This action cannot be undone."
      >
        <div className="space-y-4">
          <p className="text-xs text-neutral-600 dark:text-dark-textMuted">
            Session to delete:{' '}
            <span className="font-mono font-semibold text-neutral-900 dark:text-dark-text">
              {pendingDelete?.original_filename ?? pendingDelete?.id}
            </span>
          </p>
          {deleteError && (
            <div
              role="alert"
              className="p-3 rounded-md border border-semantic-error/30 bg-semantic-error/5 text-xs text-neutral-700 dark:text-neutral-300"
            >
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
              Cancel
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => void confirmDelete()}
              isLoading={isDeleting}
              leftIcon={<Trash2 className="w-3.5 h-3.5" />}
            >
              Yes, Delete
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default History;
