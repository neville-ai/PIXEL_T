import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '@/context/AuthContext';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  Eye,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';

// --- Types ---

interface DoctorItem {
  id: string;
  user_id: string;
  full_name: string;
  email: string;
  hospital?: string;
  primary_specialty?: string;
  account_status: 'pending' | 'approved' | 'rejected';
  created_at: string;
  approved_at?: string;
  rejection_reason?: string | null;
}

interface Stats {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
}

// --- API helpers ---

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000';

async function fetchAdminDoctors(token: string, status?: string): Promise<{ success: boolean; data?: DoctorItem[] }> {
  const params = status ? `?status=${status}` : '';
  const res = await fetch(`${API_BASE}/api/admin/doctors${params}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function fetchAdminStats(token: string): Promise<{ success: boolean; data?: Stats }> {
  const res = await fetch(`${API_BASE}/api/admin/doctors/stats`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function fetchAdminDoctorDetail(token: string, doctorId: string): Promise<{ success: boolean; data?: DoctorItem }> {
  const res = await fetch(`${API_BASE}/api/admin/doctors/${doctorId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function approveDoctor(token: string, doctorId: string): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/api/admin/doctors/${doctorId}/approve`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function rejectDoctor(token: string, doctorId: string, reason?: string): Promise<{ success: boolean }> {
  const res = await fetch(`${API_BASE}/api/admin/doctors/${doctorId}/reject`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: reason ? JSON.stringify({ reason }) : undefined,
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// --- Error message mapping ---

// Tampilkan pesan ramah pengguna tanpa bocorkan detail internal (kode, traceback, dsb).
function describeApiError(e: unknown, fallback: string): string {
  if (e instanceof Error) {
    const m = e.message;
    if (m === 'HTTP 401') return 'Sesi Anda telah berakhir. Silakan login kembali.';
    if (m === 'HTTP 403') return 'Akses ditolak. Anda tidak memiliki izin untuk melakukan aksi ini.';
    if (m === 'HTTP 404') return 'Data tidak ditemukan pada server.';
    if (m === 'HTTP 409') return 'Data telah berubah. Muat ulang daftar lalu coba lagi.';
    if (m === 'HTTP 422') return 'Permintaan tidak valid.';
    if (/^HTTP 5\d\d$/.test(m)) return `${fallback} Server sedang mengalami gangguan, coba lagi.`;
    if (m.startsWith('HTTP ')) return fallback;
    // TypeError biasanya muncul saat jaringan putus (fetch gagal).
    return 'Tidak dapat terhubung ke server. Periksa koneksi internet Anda.';
  }
  return fallback;
}

// --- Status badge helper ---

function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case 'pending':
      return (
        <Badge variant="warning">
          <Clock className="w-3 h-3 mr-1" />
          Pending
        </Badge>
      );
    case 'approved':
      return (
        <Badge variant="success">
          <CheckCircle2 className="w-3 h-3 mr-1" />
          Approved
        </Badge>
      );
    case 'rejected':
      return (
        <Badge variant="error">
          <XCircle className="w-3 h-3 mr-1" />
          Rejected
        </Badge>
      );
    default:
      return <Badge variant="default">{status}</Badge>;
  }
}

// --- Stat Card ---

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: number;
  color: string;
}) {
  return (
    <Card>
      <div className="flex items-center gap-4">
        <div className={`w-11 h-11 rounded-lg flex items-center justify-center shrink-0 ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
        <div>
          <p className="text-2xl font-bold text-neutral-900 dark:text-dark-text">{value}</p>
          <p className="text-sm text-neutral-500 dark:text-dark-textMuted">{label}</p>
        </div>
      </div>
    </Card>
  );
}

// --- Main Page ---

export const AdminDashboard: React.FC = () => {
  const { user, session } = useAuth();
  const navigate = useNavigate();

  const [doctors, setDoctors] = useState<DoctorItem[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'rejected'>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);       // kegagalan memuat daftar dokter
  const [statsError, setStatsError] = useState<string | null>(null); // kegagalan statistik (non-blokir)
  const [actionError, setActionError] = useState<string | null>(null); // kegagalan approve/tolak
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Detail modal state
  const [selectedDoctor, setSelectedDoctor] = useState<DoctorItem | null>(null);
  const [showDetail, setShowDetail] = useState(false);

  // Reject reason modal state
  const [rejectReason, setRejectReason] = useState('');
  const [confirmRejectId, setConfirmRejectId] = useState<string | null>(null);

  const token = session?.access_token ?? '';

  // Mencegah response lewat dari request filtering yang lebih lama menimpa data baru.
  const listSeqRef = useRef(0);

  const loadDoctors = useCallback(async (statusFilter?: string) => {
    if (!token) return;
    const seq = ++listSeqRef.current;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchAdminDoctors(token, statusFilter);
      // Abaikan response yang sudah ketinggalan (antrian filtering).
      if (seq !== listSeqRef.current) return;
      if (res.success && res.data !== undefined) {
        setDoctors(res.data);
      }
    } catch (e) {
      if (seq !== listSeqRef.current) return;
      setError(describeApiError(e, 'Gagal memuat data pendaftaran dokter.'));
    } finally {
      if (seq === listSeqRef.current) setLoading(false);
    }
  }, [token]);

  const loadStats = useCallback(async () => {
    if (!token) return;
    setStatsError(null);
    try {
      const res = await fetchAdminStats(token);
      if (res.success && res.data !== undefined) {
        setStats(res.data);
      }
    } catch (e) {
      // Statistik gagal tidak boleh menghilangkan daftar dokter yang sudah termuat.
      setStatsError(describeApiError(e, 'Gagal memuat statistik.'));
    }
  }, [token]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  useEffect(() => {
    loadDoctors(filter === 'all' ? undefined : filter);
  }, [filter, loadDoctors]);

  const handleApprove = async (doctorId: string) => {
    if (!token) return;
    setActionLoading(doctorId);
    setActionError(null);
    try {
      await approveDoctor(token, doctorId);
      await loadDoctors(filter === 'all' ? undefined : filter);
      await loadStats();
    } catch (e) {
      setActionError(describeApiError(e, 'Gagal menyetujui dokter.'));
    } finally {
      setActionLoading(null);
    }
  };

  const handleRejectOpen = (doctorId: string) => {
    setConfirmRejectId(doctorId);
    setRejectReason('');
  };

  const handleRejectConfirm = async () => {
    if (!token || !confirmRejectId) return;
    setActionLoading(confirmRejectId);
    setActionError(null);
    try {
      await rejectDoctor(token, confirmRejectId, rejectReason || undefined);
      setConfirmRejectId(null);
      setRejectReason('');
      await loadDoctors(filter === 'all' ? undefined : filter);
      await loadStats();
    } catch (e) {
      setActionError(describeApiError(e, 'Gagal menolak dokter.'));
    } finally {
      setActionLoading(null);
    }
  };

  const handleViewDetails = async (doctor: DoctorItem) => {
    setSelectedDoctor(doctor);
    setShowDetail(true);
    try {
      const res = await fetchAdminDoctorDetail(token, doctor.id);
      if (res.success && res.data !== undefined) {
        setSelectedDoctor(res.data);
      }
    } catch {
      // Keep the list item as fallback
    }
  };

  if (!user) {
    navigate('/login');
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-neutral-900 dark:text-dark-text">Admin Dashboard</h1>
        <p className="text-neutral-500 dark:text-dark-textMuted mt-1">
          Kelola pendaftaran akun dokter yang masuk.
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Users} label="Total Pendaftaran" value={stats?.total ?? 0} color="bg-primary-100 dark:bg-dark-accentSurface" />
        <StatCard icon={Clock} label="Menunggu Persetujuan" value={stats?.pending ?? 0} color="bg-amber-100 dark:bg-amber-900/30" />
        <StatCard icon={CheckCircle2} label="Disetujui" value={stats?.approved ?? 0} color="bg-emerald-100 dark:bg-emerald-900/30" />
        <StatCard icon={XCircle} label="Ditolak" value={stats?.rejected ?? 0} color="bg-red-100 dark:bg-red-900/30" />
      </div>

      {/* Stats error — non-blocking: daftar dokter tetap ditampilkan */}
      {statsError && (
        <div
          role="alert"
          className="flex items-center justify-between gap-3 rounded-md border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 px-4 py-2 text-sm text-amber-800 dark:text-amber-300"
        >
          <span>{statsError}</span>
          <button type="button" onClick={() => loadStats()} className="font-medium underline shrink-0">
            Coba lagi
          </button>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2 flex-wrap">
        {(['all', 'pending', 'approved', 'rejected'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              filter === f
                ? 'bg-primary-600 text-white'
                : 'bg-white dark:bg-dark-surface text-neutral-600 dark:text-dark-textMuted border border-neutral-200 dark:border-dark-border hover:bg-neutral-50 dark:hover:bg-dark-elevated'
            }`}
          >
            {f === 'all' && 'Semua'}
            {f === 'pending' && 'Pending'}
            {f === 'approved' && 'Disetujui'}
            {f === 'rejected' && 'Ditolak'}
            {f !== 'all' && ` (${stats?.[f] ?? 0})`}
          </button>
        ))}
      </div>

      {/* Action error — non-blocking: tabel tetap terlihat, admin bisa mencoba lagi */}
      {actionError && (
        <div
          role="alert"
          className="flex items-center justify-between gap-3 rounded-md border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 px-4 py-2 text-sm text-red-700 dark:text-red-400"
        >
          <span>{actionError}</span>
          <button type="button" onClick={() => setActionError(null)} className="font-medium underline shrink-0">
            Tutup
          </button>
        </div>
      )}

      {/* Doctor List */}
      {loading ? (
        <LoadingState title="Memuat Data" description="Mengambil daftar pendaftaran dokter..." />
      ) : error ? (
        <ErrorState message={error} onRetry={() => loadDoctors(filter === 'all' ? undefined : filter)} />
      ) : doctors.length === 0 ? (
        <EmptyState
          icon={<Users className="w-6 h-6" />}
          title="Belum ada pendaftaran"
          description="Belum ada dokter yang mendaftarkan akun."
        />
      ) : (
        <div className="border border-neutral-200 dark:border-dark-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-neutral-50 dark:bg-dark-surface border-b border-neutral-200 dark:border-dark-border">
                <th className="text-left px-4 py-3 font-medium text-neutral-600 dark:text-dark-textMuted">Nama</th>
                <th className="text-left px-4 py-3 font-medium text-neutral-600 dark:text-dark-textMuted hidden sm:table-cell">Email</th>
                <th className="text-left px-4 py-3 font-medium text-neutral-600 dark:text-dark-textMuted hidden md:table-cell">Rumah Sakit</th>
                <th className="text-left px-4 py-3 font-medium text-neutral-600 dark:text-dark-textMuted hidden lg:table-cell">Spesialisasi</th>
                <th className="text-left px-4 py-3 font-medium text-neutral-600 dark:text-dark-textMuted">Status</th>
                <th className="text-left px-4 py-3 font-medium text-neutral-600 dark:text-dark-textMuted hidden md:table-cell">Terdaftar</th>
                <th className="text-right px-4 py-3 font-medium text-neutral-600 dark:text-dark-textMuted">Aksi</th>
              </tr>
            </thead>
            <tbody>
              {doctors.map((doc) => (
                <tr key={doc.id} className="border-b border-neutral-100 dark:border-dark-border hover:bg-neutral-50 dark:hover:bg-dark-elevated/50 transition-colors">
                  <td className="px-4 py-3">
                    <span className="font-medium text-neutral-900 dark:text-dark-text">{doc.full_name}</span>
                  </td>
                  <td className="px-4 py-3 text-neutral-500 dark:text-dark-textMuted hidden sm:table-cell">{doc.email || '—'}</td>
                  <td className="px-4 py-3 text-neutral-500 dark:text-dark-textMuted hidden md:table-cell">{doc.hospital || '—'}</td>
                  <td className="px-4 py-3 text-neutral-500 dark:text-dark-textMuted hidden lg:table-cell">{doc.primary_specialty || '—'}</td>
                  <td className="px-4 py-3">
                    <StatusBadge status={doc.account_status} />
                  </td>
                  <td className="px-4 py-3 text-neutral-500 dark:text-dark-textMuted hidden md:table-cell">
                    {doc.created_at ? new Date(doc.created_at).toLocaleDateString('id-ID') : '—'}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewDetails(doc)}
                      >
                        <Eye className="w-4 h-4" />
                        <span className="hidden sm:inline">Detail</span>
                      </Button>
                      {doc.account_status === 'pending' && (
                        <>
                          <Button
                            variant="accent"
                            size="sm"
                            onClick={() => handleApprove(doc.id)}
                            disabled={actionLoading === doc.id}
                          >
                            {actionLoading === doc.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                            <span className="hidden sm:inline">Setujui</span>
                          </Button>
                          <Button
                            variant="danger"
                            size="sm"
                            onClick={() => handleRejectOpen(doc.id)}
                            disabled={actionLoading === doc.id}
                          >
                            {actionLoading === doc.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                            <span className="hidden sm:inline">Tolak</span>
                          </Button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Detail Modal */}
      <Modal
        isOpen={showDetail}
        onClose={() => setShowDetail(false)}
        title="Detail Pendaftaran Dokter"
        maxWidthClass="max-w-lg"
      >
        {selectedDoctor && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-neutral-500 dark:text-dark-textMuted">Nama Lengkap</p>
                <p className="font-medium text-neutral-900 dark:text-dark-text">{selectedDoctor.full_name}</p>
              </div>
              <div>
                <p className="text-neutral-500 dark:text-dark-textMuted">Email</p>
                <p className="font-medium text-neutral-900 dark:text-dark-text">{selectedDoctor.email || '—'}</p>
              </div>
              <div>
                <p className="text-neutral-500 dark:text-dark-textMuted">Rumah Sakit</p>
                <p className="font-medium text-neutral-900 dark:text-dark-text">{selectedDoctor.hospital || '—'}</p>
              </div>
              <div>
                <p className="text-neutral-500 dark:text-dark-textMuted">Spesialisasi</p>
                <p className="font-medium text-neutral-900 dark:text-dark-text">{selectedDoctor.primary_specialty || '—'}</p>
              </div>
              <div>
                <p className="text-neutral-500 dark:text-dark-textMuted">Status</p>
                <div className="mt-1"><StatusBadge status={selectedDoctor.account_status} /></div>
              </div>
              <div>
                <p className="text-neutral-500 dark:text-dark-textMuted">Tanggal Daftar</p>
                <p className="font-medium text-neutral-900 dark:text-dark-text">
                  {selectedDoctor.created_at
                    ? new Date(selectedDoctor.created_at).toLocaleDateString('id-ID', { year: 'numeric', month: 'long', day: 'numeric' })
                    : '—'}
                </p>
              </div>
            </div>
            {selectedDoctor.rejection_reason && (
              <div className="p-3 rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                <p className="text-xs font-semibold text-red-700 dark:text-red-400 mb-1">Alasan Penolakan</p>
                <p className="text-sm text-red-600 dark:text-red-300">{selectedDoctor.rejection_reason}</p>
              </div>
            )}
            {selectedDoctor.approved_at && (
              <p className="text-xs text-neutral-400 dark:text-dark-textMuted">
                Disetujui pada {new Date(selectedDoctor.approved_at).toLocaleString('id-ID')}
              </p>
            )}
          </div>
        )}
      </Modal>

      {/* Reject Confirmation Modal */}
      <Modal
        isOpen={confirmRejectId !== null}
        onClose={() => { setConfirmRejectId(null); setRejectReason(''); }}
        title="Tolak Pendaftaran"
        description="Apakah Anda yakin ingin menolak pendaftaran dokter ini? Tindakan ini tidak dapat dibatalkan."
        maxWidthClass="max-w-md"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-dark-text mb-1">
              Alasan penolakan (opsional)
            </label>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              rows={3}
              className="w-full rounded-md border border-neutral-300 dark:border-dark-border bg-white dark:bg-dark-surface px-3 py-2 text-sm text-neutral-900 dark:text-dark-text placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-accent-500"
              placeholder="Masukkan alasan penolakan..."
            />
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="ghost" onClick={() => { setConfirmRejectId(null); setRejectReason(''); }}>
              Batal
            </Button>
            <Button
              variant="danger"
              onClick={handleRejectConfirm}
              disabled={actionLoading === confirmRejectId}
            >
              {actionLoading === confirmRejectId ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <XCircle className="w-4 h-4 mr-2" />
              )}
              Tolak Pendaftaran
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default AdminDashboard;
