import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { supabase } from '@/lib/supabase';
import type { User } from '@supabase/supabase-js';
import { useAuth } from '@/context/AuthContext';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { LoadingState } from '@/components/ui/LoadingState';
import { listHistory, type HistoryItem } from '@/services/analysis';
import { formatAnalysisDate, getDisplayName, getUserInitials } from '@/lib/format';
import {
  fetchDoctorProfile,
  saveDoctorProfile,
  uploadAvatar,
  deleteAvatar,
  type DoctorProfileData,
} from '@/services/profile';
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  Building2,
  Calendar,
  Camera,
  Check,
  CheckCircle2,
  Edit3,
  FileText,
  ImageOff,
  Loader2,
} from 'lucide-react';

const RECENT_LIMIT = 3;

interface ActivityStats {
  total: number;
  completed: number;
  processing: number;
  failed: number;
}

function computeStats(items: HistoryItem[]): ActivityStats {
  let completed = 0;
  let processing = 0;
  let failed = 0;

  for (const item of items) {
    if (item.status === 'completed') completed += 1;
    else if (item.status === 'processing') processing += 1;
    else if (item.status === 'failed') failed += 1;
  }

  return { total: items.length, completed, processing, failed };
}

function calculateAge(birthDateString?: string): number | null {
  if (!birthDateString) return null;
  const birth = new Date(birthDateString);
  if (isNaN(birth.getTime())) return null;
  const now = new Date();
  let age = now.getFullYear() - birth.getFullYear();
  const m = now.getMonth() - birth.getMonth();
  if (m < 0 || (m === 0 && now.getDate() < birth.getDate())) {
    age--;
  }
  return age >= 0 ? age : null;
}

interface StatusPresentation {
  variant: 'success' | 'accent' | 'error';
  icon: React.ReactNode;
  label: string;
}

function statusPresentation(status: HistoryItem['status']): StatusPresentation {
  if (status === 'failed') {
    return {
      variant: 'error',
      icon: <AlertCircle className="w-3 h-3" aria-hidden="true" />,
      label: 'Failed',
    };
  }
  if (status === 'processing') {
    return {
      variant: 'accent',
      icon: <Loader2 className="w-3 h-3" aria-hidden="true" />,
      label: 'Processing',
    };
  }
  return {
    variant: 'success',
    icon: <CheckCircle2 className="w-3 h-3" aria-hidden="true" />,
    label: 'Completed',
  };
}

const RecentThumb: React.FC<{ item: HistoryItem }> = ({ item }) => {
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
  if (item.status === 'processing') {
    return <Loader2 className="w-4 h-4 animate-spin text-accent-600 dark:text-accent-500" aria-hidden="true" />;
  }
  if (item.status === 'failed') {
    return <ImageOff className="w-4 h-4 text-semantic-error" aria-hidden="true" />;
  }
  return <FileText className="w-4 h-4" aria-hidden="true" />;
};

const SectionLabel: React.FC<{ children: React.ReactNode; right?: React.ReactNode }> = ({
  children,
  right,
}) => (
  <div className="mb-4 flex items-center justify-between gap-3 border-b border-neutral-100 pb-3 dark:border-dark-border">
    <span className="font-mono text-[11px] uppercase tracking-wider text-neutral-500 dark:text-dark-textMuted">
      {children}
    </span>
    {right}
  </div>
);

interface StatCardProps {
  label: string;
  value: number;
  caption: string;
  captionVariant: 'default' | 'success' | 'accent' | 'error';
  valueClassName: string;
}

const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  caption,
  captionVariant,
  valueClassName,
}) => (
  <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3 dark:border-dark-border dark:bg-dark-elevated/40">
    <p className="font-mono text-[10px] uppercase tracking-wider text-neutral-500 dark:text-dark-textMuted">
      {label}
    </p>
    <div className="mt-1.5 flex items-end justify-between gap-2">
      <span className={`text-2xl font-bold tabular-nums leading-none ${valueClassName}`}>{value}</span>
      <Badge variant={captionVariant} size="sm" uppercase={false}>
        {caption}
      </Badge>
    </div>
  </div>
);

const IdentityRow: React.FC<{ label: string; children: React.ReactNode }> = ({ label, children }) => (
  <div className="flex flex-col gap-1 py-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
    <dt className="shrink-0 font-mono text-[11px] uppercase tracking-wider text-neutral-500 dark:text-dark-textMuted">
      {label}
    </dt>
    <dd className="min-w-0 break-all text-sm text-neutral-900 dark:text-dark-text">{children}</dd>
  </div>
);

// ---------------------------------------------------------------------------
// Section edit-modal helpers
// ---------------------------------------------------------------------------

type EditSection = 'A' | 'B' | 'C';

interface SectionModalState {
  section: EditSection | null;
  isOpen: boolean;
}

/** Returns only the fields belonging to the requested section for the modal form. */
function pickSectionFields(profile: DoctorProfileData, section: EditSection): DoctorProfileData {
  switch (section) {
    case 'A': // Clinician Profile
      return {
        fullName: profile.fullName ?? '',
        education: profile.education ?? [],
        experience: profile.experience ?? [],
        professionCategory: profile.professionCategory,
        academicTitle: profile.academicTitle,
        primarySpecialty: profile.primarySpecialty,
        subspecialty: profile.subspecialty,
        clinicalFocus: profile.clinicalFocus,
      };
    case 'B': // Personal Information
      return {
        fullName: profile.fullName,
        phone: profile.phone,
        birthDate: profile.birthDate,
        city: profile.city,
        education: [],
        experience: [],
      };
    case 'C': // Hospital Affiliation
      return {
        fullName: profile.fullName ?? '',
        education: profile.education ?? [],
        experience: profile.experience ?? [],
        hospital: profile.hospital,
        department: profile.department,
        clinicalRole: profile.clinicalRole,
        yearsExperience: profile.yearsExperience,
        practiceAddress: profile.practiceAddress,
      };
  }
}

const SECTION_MODAL_CONFIG: Record<
  EditSection,
  { title: string; description: string; fields: Array<{ key: string; label: string; placeholder: string }> }
> = {
  A: {
    title: 'Edit Clinical Details',
    description: 'Update your specialization, academic title, and clinical focus.',
    fields: [
      { key: 'professionCategory', label: 'Kategori / Profesi Dokter', placeholder: 'e.g. Dokter Spesialis Penyakit Dalam' },
      { key: 'academicTitle', label: 'Gelar Akademik (Academic Title)', placeholder: 'e.g. Sp.PD-KGEH, FINASIM' },
      { key: 'primarySpecialty', label: 'Spesialisasi Utama', placeholder: 'e.g. Gastroenterologi Hepatologi' },
      { key: 'subspecialty', label: 'Subspesialisasi', placeholder: 'e.g. Endoskopi Saluran Cerna' },
      { key: 'clinicalFocus', label: 'Fokus Klinis', placeholder: 'e.g. Gastrointestinal Endoscopy' },
    ],
  },
  B: {
    title: 'Edit Personal Information',
    description: 'Update your personal details.',
    fields: [
      { key: 'fullName', label: 'Nama Lengkap', placeholder: 'e.g. Dr. Neville' },
      { key: 'phone', label: 'Nomor Telepon', placeholder: 'e.g. +62 812 3456 7890' },
      { key: 'birthDate', label: 'Tanggal Lahir', placeholder: 'e.g. 1985-05-20' },
      { key: 'city', label: 'Kota / Domisili', placeholder: 'e.g. Yogyakarta, Indonesia' },
    ],
  },
  C: {
    title: 'Edit Hospital Affiliation',
    description: 'Update your hospital and affiliation details.',
    fields: [
      { key: 'hospital', label: 'Rumah Sakit / Institusi', placeholder: 'e.g. RSUP Dr. Sardjito Yogyakarta' },
      { key: 'department', label: 'Departemen / Unit', placeholder: 'e.g. Instalasi Endoskopi' },
      { key: 'clinicalRole', label: 'Peran Klinis', placeholder: 'e.g. Attending Physician' },
      { key: 'yearsExperience', label: 'Tahun Pengalaman', placeholder: 'e.g. 12' },
      { key: 'practiceAddress', label: 'Alamat Praktik', placeholder: 'e.g. Jl. Kesehatan No. 1' },
    ],
  },
};

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export const DoctorProfile: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Activity stats state
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [isActivityLoading, setIsActivityLoading] = useState(true);
  const [activityError, setActivityError] = useState<string | null>(null);

  // Profile data state
  const [profile, setProfile] = useState<DoctorProfileData>({
    fullName: '',
    education: [],
    experience: [],
  });
  const [isProfileLoading, setIsProfileLoading] = useState(true);
  const [profileError, setProfileError] = useState<string | null>(null);

  // Section-specific edit modal state
  const [modalState, setModalState] = useState<SectionModalState>({ section: null, isOpen: false });
  const [editFormData, setEditFormData] = useState<DoctorProfileData>({
    fullName: '',
    education: [],
    experience: [],
  });
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Avatar upload state
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const [avatarError, setAvatarError] = useState<string | null>(null);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const [isDeletingAvatar, setIsDeletingAvatar] = useState(false);
  const avatarInputRef = useRef<HTMLInputElement>(null);

  // Load analysis activity
  const loadActivity = useCallback(async () => {
    setIsActivityLoading(true);
    setActivityError(null);
    try {
      const result = await listHistory();
      setItems(result.items ?? []);
    } catch (error) {
      setItems([]);
      setActivityError(error instanceof Error ? error.message : 'Failed to load analysis activity.');
    } finally {
      setIsActivityLoading(false);
    }
  }, []);

  // Load doctor profile
  const loadProfile = useCallback(async (activeUser: User | null) => {
    if (!activeUser) {
      setIsProfileLoading(false);
      return;
    }
    setIsProfileLoading(true);
    setProfileError(null);
    try {
      const data = await fetchDoctorProfile(activeUser);
      setProfile(data);
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : 'Gagal memuat profil dokter.');
    } finally {
      setIsProfileLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadActivity();
  }, [loadActivity]);

  useEffect(() => {
    void loadProfile(user);
  }, [user, loadProfile]);

  // Avatar handlers
  const handleUploadAvatar = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !user) return;
    setIsUploadingAvatar(true);
    setAvatarError(null);
    const { data: sessionData } = await supabase.auth.getSession();
    if (!sessionData.session) {
      setAvatarError('Sesi autentikasi tidak ditemukan. Silakan login ulang.');
      setIsUploadingAvatar(false);
      if (avatarInputRef.current) avatarInputRef.current.value = '';
      return;
    }
    const result = await uploadAvatar(user, file);
    setIsUploadingAvatar(false);
    if (result.error) {
      setAvatarError(result.error);
      return;
    }
    if (!result.url) return;
    try {
      const saveResult = await saveDoctorProfile(user, { ...profile, avatarUrl: result.url });
      if (saveResult.error) {
        setAvatarError(saveResult.error);
        return;
      }
      setProfile((prev) => ({ ...prev, avatarUrl: result.url }));
    } catch (err) {
      setAvatarError(err instanceof Error ? err.message : 'Gagal menyimpan foto.');
    }
    if (avatarInputRef.current) avatarInputRef.current.value = '';
  }, [user, profile, supabase]);

  const handleOpenDeleteConfirm = useCallback(() => {
    setAvatarError(null);
    setIsDeleteConfirmOpen(true);
  }, []);

  const handleCloseDeleteConfirm = useCallback(() => {
    setIsDeleteConfirmOpen(false);
    setAvatarError(null);
  }, []);

  const handleDeleteAvatar = useCallback(async () => {
    if (!user) return;
    setIsDeletingAvatar(true);
    const result = await deleteAvatar(user);
    setIsDeletingAvatar(false);
    if (result.error) {
      setAvatarError(result.error);
      return;
    }
    try {
      const saveResult = await saveDoctorProfile(user, { ...profile, avatarUrl: undefined });
      if (saveResult.error) {
        setAvatarError(saveResult.error);
        return;
      }
      setProfile((prev) => ({ ...prev, avatarUrl: undefined }));
    } catch (err) {
      setAvatarError(err instanceof Error ? err.message : 'Gagal menghapus referensi foto.');
    }
    setIsDeleteConfirmOpen(false);
  }, [user, profile]);

  // Derived Profile Values
  const effectiveDisplayName = useMemo(() => {
    if (profile.fullName?.trim()) {
      return profile.academicTitle?.trim()
        ? `${profile.fullName.trim()}, ${profile.academicTitle.trim()}`
        : profile.fullName.trim();
    }
    return getDisplayName(user);
  }, [profile.fullName, profile.academicTitle, user]);

  const initials = getUserInitials(effectiveDisplayName);
  const stats = useMemo(() => computeStats(items), [items]);
  const recent = useMemo(() => items.slice(0, RECENT_LIMIT), [items]);
  const calculatedAge = useMemo(() => calculateAge(profile.birthDate), [profile.birthDate]);

  // ---- Section edit modal handlers ----

  const openSectionEdit = useCallback((section: EditSection) => {
    const formData = pickSectionFields(profile, section);
    setEditFormData(formData);
    setSaveError(null);
    setModalState({ section, isOpen: true });
  }, [profile]);

  const closeSectionEditModal = useCallback(() => {
    if (!isSaving) {
      setModalState(prev => ({ ...prev, isOpen: false }));
    }
  }, [isSaving]);

  const handleSectionSave = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user || !modalState.section) return;
    setIsSaving(true);
    setSaveError(null);

    // Merge edited section fields back into the full profile to preserve other sections
    const merged: DoctorProfileData = {
      ...profile,
      ...editFormData,
      updatedAt: new Date().toISOString(),
    };

    const result = await saveDoctorProfile(user, merged);
    if (result.error) {
      setSaveError(result.error);
      setIsSaving(false);
      return;
    }

    if (result.data) {
      setProfile(result.data);
      setIsSaving(false);
      setModalState(prev => ({ ...prev, isOpen: false }));
      setSaveSuccessMsg('Profil berhasil diperbarui dan disimpan.');
      window.setTimeout(() => setSaveSuccessMsg(null), 4000);
    }
  }, [user, modalState.section, editFormData, profile]);

  if (isProfileLoading && !profile.fullName) {
    return (
      <div className="py-12">
        <LoadingState
          title="Loading Doctor Profile"
          description="Fetching clinician profile and account details..."
        />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Breadcrumb + Header */}
      <div className="space-y-3 border-b border-neutral-200 pb-6 dark:border-dark-border">
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-1 text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200"
          >
            <ArrowLeft className="w-3.5 h-3.5" aria-hidden="true" /> Dashboard
          </Link>
          <span className="text-neutral-300 dark:text-neutral-700" aria-hidden="true">
            /
          </span>
          <span className="text-neutral-500 dark:text-dark-textMuted">
            Doctor Profile &amp; Account Information
          </span>
        </div>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="space-y-1">
            <h1 className="text-2xl font-bold tracking-tight text-neutral-900 sm:text-3xl dark:text-dark-text">
              Doctor Profile &amp; Account Information
            </h1>
            <p className="max-w-2xl text-sm leading-relaxed text-neutral-600 dark:text-dark-textMuted">
              Manage your professional clinician profile, affiliation details, and review your PIXEL-T analysis activity.
            </p>
          </div>
        </div>
      </div>

      {/* Success Notification Banner */}
      {saveSuccessMsg && (
        <div className="flex items-center gap-3 rounded-lg border border-accent-600/30 bg-accent-50 p-4 text-sm text-accent-900 dark:border-accent-500/30 dark:bg-dark-accentSurface dark:text-accent-300">
          <CheckCircle2 className="h-5 w-5 shrink-0 text-accent-600 dark:text-accent-400" />
          <p className="font-medium">{saveSuccessMsg}</p>
        </div>
      )}

      {profileError && (
        <ErrorState
          code="PROFILE_LOAD_FAILED"
          message={profileError}
          onRetry={() => void loadProfile(user)}
        />
      )}

      {/* Main Grid: Left column = Sections A, B, C | Right column = PIXEL-T Activity */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* ========================================================================= */}
        {/* LEFT COLUMN: Section A (Clinician Profile) + Section B (Personal Info) + Section C (Hospital) */}
        {/* ========================================================================= */}
        <div className="space-y-6">

          {/* ========================================================= */}
          {/* Section A: Clinician Profile */}
          {/* ========================================================= */}
          <Card>
            <SectionLabel
              right={
                profile.isVerified ? (
                  <span className="inline-flex items-center gap-1.5 font-mono text-[11px] font-semibold uppercase tracking-wider text-accent-700 dark:text-accent-400">
                    <span className="h-2 w-2 rounded-full bg-accent-600 dark:bg-accent-400 animate-pulse" />
                    Verified Clinician
                  </span>
                ) : null
              }
            >
              Section A // Clinician Profile
            </SectionLabel>

            <div className="flex flex-col items-center gap-3 py-2 text-center">
              <div className="relative group">
                {profile.avatarUrl ? (
                  <img
                    src={profile.avatarUrl}
                    alt={`${effectiveDisplayName || 'User'} avatar`}
                    className="h-24 w-24 rounded-full border-2 border-accent-600/40 object-cover shadow-sm"
                  />
                ) : (
                  <span
                    aria-hidden="true"
                    className="inline-flex h-24 w-24 items-center justify-center rounded-full border-2 border-accent-600/40 bg-accent-100 text-2xl font-bold tracking-wide text-accent-700 dark:bg-dark-accentSurface dark:text-accent-500 shadow-sm"
                  >
                    {initials || '?'}
                  </span>
                )}
                {profile.isVerified && (
                  <span
                    title="Verified Account"
                    className="absolute bottom-0 right-0 flex h-6 w-6 items-center justify-center rounded-full bg-accent-600 text-white shadow"
                  >
                    <Check className="h-3.5 w-3.5 stroke-[3]" />
                  </span>
                )}
                <label
                  title={profile.avatarUrl ? 'Ganti foto profil' : 'Tambah foto profil'}
                  className="absolute inset-0 flex items-center justify-center rounded-full bg-black/40 opacity-0 transition-opacity group-hover:opacity-100 cursor-pointer"
                >
                  <Camera className="h-5 w-5 text-white" aria-hidden="true" />
                  <input
                    ref={avatarInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    className="hidden"
                    onChange={handleUploadAvatar}
                    aria-label={profile.avatarUrl ? 'Ganti foto profil' : 'Tambah foto profil'}
                  />
                </label>
              </div>

              <div className="space-y-1">
                <div className="flex items-center justify-center gap-2">
                  <h2 className="text-xl font-bold text-neutral-900 dark:text-dark-text">
                    {effectiveDisplayName || 'Pengguna'}
                  </h2>
                  {profile.isVerified && (
                    <CheckCircle2 className="h-4 w-4 text-accent-600 dark:text-accent-400" aria-label="Verified" />
                  )}
                </div>
                {user?.email && (
                  <p className="text-sm font-medium text-neutral-500 dark:text-dark-textMuted">{user.email}</p>
                )}
              </div>
            </div>

            {/* Avatar actions */}
            {avatarError && (
              <p className="text-xs text-semantic-error dark:text-red-400">{avatarError}</p>
            )}
            {profile.avatarUrl && (
              <button
                type="button"
                className="text-xs text-neutral-500 hover:text-semantic-error dark:text-dark-textMuted dark:hover:text-red-400 transition-colors"
                onClick={handleOpenDeleteConfirm}
              >
                Hapus Foto
              </button>
            )}
            {isUploadingAvatar && (
              <p className="text-xs text-neutral-500 dark:text-dark-textMuted">Mengunggah foto...</p>
            )}

            {/* Specialization & Credentials Box */}
            <div className="mt-4 space-y-3 rounded-lg border border-neutral-200 bg-white p-4 dark:border-dark-border dark:bg-dark-surface">
              <div>
                <p className="font-mono text-[10px] uppercase tracking-wider text-neutral-500 dark:text-dark-textMuted">
                  Specialization &amp; Credentials
                </p>
                <p className="mt-1 text-sm font-semibold text-neutral-900 dark:text-dark-text">
                  {profile.professionCategory || profile.primarySpecialty
                    ? `${profile.professionCategory || 'Dokter Spesialis'}${
                        profile.primarySpecialty ? ` — Konsultan ${profile.primarySpecialty}` : ''
                      }${profile.academicTitle ? ` (${profile.academicTitle})` : ''}`
                    : 'Belum diisi'}
                </p>
                {profile.subspecialty && (
                  <p className="mt-0.5 text-xs text-neutral-600 dark:text-dark-textMuted">
                    Subspesialisasi: {profile.subspecialty}
                  </p>
                )}
              </div>

              <div className="border-t border-neutral-100 pt-3 dark:border-dark-border">
                <p className="font-mono text-[10px] uppercase tracking-wider text-neutral-500 dark:text-dark-textMuted">
                  Clinical Focus
                </p>
                <p className="mt-1 text-xs font-medium text-accent-700 dark:text-accent-400">
                  {profile.clinicalFocus || 'Gastrointestinal Endoscopy & Colorectal Screening'}
                </p>
              </div>
            </div>

            <div className="mt-4 flex justify-end">
              <Button
                type="button"
                variant="outline"
                size="sm"
                leftIcon={<Edit3 className="w-3.5 h-3.5" />}
                onClick={() => openSectionEdit('A')}
              >
                Edit Clinical Details
              </Button>
            </div>
          </Card>

          {/* ========================================================= */}
          {/* Section B: Personal Information */}
          {/* ========================================================= */}
          <Card>
            <SectionLabel
              right={
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  leftIcon={<Edit3 className="w-3.5 h-3.5" />}
                  onClick={() => openSectionEdit('B')}
                >
                  Edit Profile
                </Button>
              }
            >
              Section B // Personal Information
            </SectionLabel>

            <div className="mb-4 space-y-1">
              <h2 className="text-base font-semibold tracking-tight text-neutral-900 dark:text-dark-text">
                Personal Information
              </h2>
              <p className="text-xs text-neutral-600 dark:text-dark-textMuted">
                Account data provided by the authentication service and clinician profile.
              </p>
            </div>

            <dl className="divide-y divide-neutral-100 dark:divide-dark-border">
              <IdentityRow label="Full Name">
                <span className="font-medium text-neutral-900 dark:text-dark-text">
                  {profile.fullName || <span className="text-neutral-400 dark:text-neutral-500">Not available</span>}
                </span>
              </IdentityRow>

              <IdentityRow label="Email Address">
                <span className="flex items-center gap-2">
                  <span>{user?.email ?? <span className="text-neutral-400 dark:text-neutral-500">Not available</span>}</span>
                  {user?.email && (
                    <Badge variant="accent" size="sm" uppercase={false}>
                      Primary
                    </Badge>
                  )}
                </span>
              </IdentityRow>

              <IdentityRow label="Phone Number">
                {profile.phone ? (
                  <span className="font-mono">{profile.phone}</span>
                ) : (
                  <span className="text-neutral-400 dark:text-neutral-500">Not available</span>
                )}
              </IdentityRow>

              <IdentityRow label="Birth Date &amp; Age">
                {profile.birthDate ? (
                  <span>
                    {profile.birthDate}
                    {calculatedAge !== null ? ` (${calculatedAge} tahun)` : ''}
                  </span>
                ) : (
                  <span className="text-neutral-400 dark:text-neutral-500">Not available</span>
                )}
              </IdentityRow>

              <IdentityRow label="City / Domicile">
                {profile.city || <span className="text-neutral-400 dark:text-neutral-500">Not available</span>}
              </IdentityRow>
            </dl>
          </Card>

          {/* ========================================================= */}
          {/* Section C: Hospital Affiliation */}
          {/* ========================================================= */}
          <Card>
            <SectionLabel
              right={
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  leftIcon={<Edit3 className="w-3.5 h-3.5" />}
                  onClick={() => openSectionEdit('C')}
                >
                  Edit Affiliation
                </Button>
              }
            >
              Section C // Hospital Affiliation
            </SectionLabel>

            <div className="flex items-start gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-neutral-200 bg-neutral-100 text-neutral-700 dark:border-dark-border dark:bg-dark-elevated dark:text-accent-400">
                <Building2 className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <h3 className="text-base font-bold text-neutral-900 dark:text-dark-text">
                  {profile.hospital || 'Belum diisi'}
                </h3>
                <p className="text-xs text-neutral-500 dark:text-dark-textMuted">
                  Clinical Diagnostic Partner Institution
                </p>
              </div>
            </div>

            <div className="mt-4 space-y-3 rounded-lg border border-neutral-200 bg-neutral-50 p-3.5 dark:border-dark-border dark:bg-dark-elevated/40 text-xs">
              <div>
                <span className="font-mono text-[10px] uppercase tracking-wider text-neutral-500 dark:text-dark-textMuted">
                  Department / Unit
                </span>
                <p className="mt-0.5 font-medium text-neutral-900 dark:text-dark-text">
                  {profile.department || 'Instalasi Endoskopi Saluran Cerna'}
                </p>
              </div>

              <div className="border-t border-neutral-200/60 pt-2.5 dark:border-dark-border">
                <span className="font-mono text-[10px] uppercase tracking-wider text-neutral-500 dark:text-dark-textMuted">
                  Clinical Role
                </span>
                <p className="mt-0.5 font-semibold text-accent-700 dark:text-accent-400">
                  {profile.clinicalRole || 'Attending Physician'}
                </p>
              </div>

              {profile.yearsExperience && (
                <div className="border-t border-neutral-200/60 pt-2.5 dark:border-dark-border flex justify-between items-center">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-neutral-500 dark:text-dark-textMuted">
                    Experience
                  </span>
                  <span className="font-medium text-neutral-800 dark:text-neutral-200">
                    {profile.yearsExperience} Tahun Praktik
                  </span>
                </div>
              )}

              {profile.practiceAddress && (
                <div className="border-t border-neutral-200/60 pt-2.5 dark:border-dark-border">
                  <span className="font-mono text-[10px] uppercase tracking-wider text-neutral-500 dark:text-dark-textMuted">
                    Practice Address
                  </span>
                  <p className="mt-0.5 text-neutral-700 dark:text-neutral-300">
                    {profile.practiceAddress}
                  </p>
                </div>
              )}

              <div className="border-t border-neutral-200/60 pt-2.5 dark:border-dark-border flex items-center justify-between">
                <span className="font-mono text-[10px] uppercase tracking-wider text-neutral-500 dark:text-dark-textMuted">
                  Affiliation Status
                </span>
                <Badge variant={profile.isVerified ? 'success' : 'accent'} size="sm" uppercase={false}>
                  {profile.isVerified ? 'Active Faculty & Staff' : 'Self-Reported'}
                </Badge>
              </div>
            </div>

            <p className="mt-3 text-[11px] leading-relaxed text-neutral-500 dark:text-dark-textMuted">
              Affiliation details reflect clinician self-declaration until institutional registry verification is completed.
            </p>
          </Card>
        </div>

        {/* ========================================================================= */}
        {/* RIGHT COLUMN: PIXEL-T Activity */}
        {/* ========================================================================= */}
        <div className="space-y-6">
          <Card>
            <div className="mb-1 flex flex-wrap items-start justify-between gap-3">
              <div className="flex items-center gap-2">
                <span
                  aria-hidden="true"
                  className="h-2 w-2 rounded-full bg-accent-600 dark:bg-accent-500"
                />
                <h2 className="text-base font-semibold tracking-tight text-neutral-900 dark:text-dark-text">
                  PIXEL-T Activity
                </h2>
              </div>
              <Link
                to="/history"
                className="inline-flex items-center gap-1 text-xs font-medium text-accent-600 hover:underline dark:text-accent-500"
              >
                View Full Analysis History
                <ArrowRight className="w-3 h-3" aria-hidden="true" />
              </Link>
            </div>
            <p className="text-xs text-neutral-600 dark:text-dark-textMuted">
              Summary of analysis session counts and processing statuses based on your history data.
            </p>

            {isActivityLoading ? (
              <div className="mt-4">
                <LoadingState
                  title="Loading analysis activity"
                  description="Fetching your analysis sessions from the server."
                />
              </div>
            ) : activityError ? (
              <div className="mt-4">
                <ErrorState
                  code="PROFILE_ACTIVITY_FAILED"
                  message={activityError}
                  onRetry={() => void loadActivity()}
                />
              </div>
            ) : (
              <>
                <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <StatCard
                    label="Total Records"
                    value={stats.total}
                    caption="Analyses"
                    captionVariant="default"
                    valueClassName="text-neutral-900 dark:text-dark-text"
                  />
                  <StatCard
                    label="Completed"
                    value={stats.completed}
                    caption="Completed"
                    captionVariant="success"
                    valueClassName="text-accent-600 dark:text-accent-500"
                  />
                  <StatCard
                    label="Processing"
                    value={stats.processing}
                    caption="Processing"
                    captionVariant="accent"
                    valueClassName="text-accent-600 dark:text-accent-500"
                  />
                  <StatCard
                    label="Failed"
                    value={stats.failed}
                    caption="Failed"
                    captionVariant="error"
                    valueClassName="text-semantic-error"
                  />
                </div>

                <h3 className="mb-2 mt-5 text-sm font-semibold text-neutral-900 dark:text-dark-text">
                  Recent Analysis Records
                </h3>

                {recent.length === 0 ? (
                  <EmptyState
                    title="No recent analyses yet"
                    description="Your saved analysis results will appear here."
                    action={
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => navigate('/analysis/new')}
                      >
                        Start New Analysis
                      </Button>
                    }
                  />
                ) : (
                  <ul className="divide-y divide-neutral-100 dark:divide-dark-border rounded-lg border border-neutral-200 dark:border-dark-border">
                    {recent.map((item) => {
                      const status = statusPresentation(item.status);
                      return (
                        <li
                          key={item.id}
                          className="flex flex-col gap-3 p-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4"
                        >
                          <div className="flex min-w-0 items-center gap-3">
                            <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-md border border-neutral-200 bg-neutral-100 text-neutral-500 dark:border-dark-border dark:bg-dark-elevated dark:text-neutral-400">
                              <RecentThumb item={item} />
                            </span>
                            <div className="min-w-0">
                              <p className="truncate font-mono text-xs font-semibold text-neutral-900 dark:text-dark-text">
                                {item.original_filename ?? 'Examination Session'}
                              </p>
                              <p className="mt-0.5 flex items-center gap-1 text-[11px] text-neutral-500 dark:text-dark-textMuted">
                                <Calendar className="w-3 h-3 shrink-0" aria-hidden="true" />
                                {formatAnalysisDate(item.created_at)}
                              </p>
                            </div>
                          </div>
                          <div className="flex shrink-0 items-center gap-3 self-start sm:self-center">
                            <Badge variant={status.variant} size="sm" icon={status.icon} uppercase={false}>
                              {status.label}
                            </Badge>
                            <Link
                              to={`/analysis/${item.id}`}
                              className="inline-flex items-center gap-1 text-xs font-medium text-accent-600 hover:underline dark:text-accent-500"
                            >
                              View Result
                              <ArrowRight className="w-3 h-3" aria-hidden="true" />
                            </Link>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </>
            )}
          </Card>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* SECTION-SPECIFIC EDIT MODAL */}
      {/* ========================================================================= */}
      {modalState.section && (
        <Modal
          isOpen={modalState.isOpen}
          onClose={closeSectionEditModal}
          title={SECTION_MODAL_CONFIG[modalState.section].title}
          description={SECTION_MODAL_CONFIG[modalState.section].description}
          maxWidthClass="max-w-2xl"
        >
          <form onSubmit={handleSectionSave} className="space-y-5">
            {saveError && (
              <div className="flex items-center gap-2 rounded-md border border-semantic-error/40 bg-red-50 p-3 text-xs text-badgeText-error dark:bg-red-950/20 dark:text-badgeText-error-dark">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{saveError}</span>
              </div>
            )}

            <div className="space-y-4">
              {SECTION_MODAL_CONFIG[modalState.section].fields.map(({ key, label, placeholder }) => (
                <div key={key}>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-neutral-700 dark:text-neutral-300">
                    {label}
                  </label>
                  <input
                    type={key === 'birthDate' ? 'date' : 'text'}
                    value={((editFormData as unknown) as Record<string, unknown>)[key] as string || ''}
                    onChange={(e) => setEditFormData({ ...editFormData, [key]: e.target.value })}
                    placeholder={placeholder}
                    className="mt-1 w-full rounded-md border border-neutral-200 bg-white px-3.5 py-2 text-sm text-neutral-900 focus:border-accent-600 focus:outline-none focus:ring-2 focus:ring-accent-600/20 dark:border-dark-border dark:bg-dark-surface dark:text-dark-text"
                  />
                </div>
              ))}
            </div>

            <div className="flex items-center justify-end gap-3 border-t border-neutral-200 pt-4 dark:border-dark-border">
              <Button
                type="button"
                variant="outline"
                disabled={isSaving}
                onClick={closeSectionEditModal}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={isSaving}
                leftIcon={isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : undefined}
              >
                {isSaving ? 'Menyimpan...' : 'Save Changes'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Delete avatar confirmation dialog */}
      <Modal
        isOpen={isDeleteConfirmOpen}
        onClose={handleCloseDeleteConfirm}
        surface="light"
        hideClose
        hideHeaderDivider
        maxWidthClass="max-w-[420px]"
        title="Hapus Foto Profil?"
        description="Apakah Anda yakin ingin menghapus foto profil? Tindakan ini akan mengembalikan avatar ke inisial Anda."
      >
        <div className="flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={handleCloseDeleteConfirm}
            disabled={isDeletingAvatar}
            className="inline-flex items-center justify-center rounded-md border border-neutral-300 bg-white h-11 px-5 text-base font-medium text-neutral-900 transition-colors hover:bg-neutral-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-500 focus-visible:ring-offset-2 disabled:opacity-50"
          >
            Batal
          </button>
          <button
            type="button"
            onClick={() => void handleDeleteAvatar()}
            disabled={isDeletingAvatar}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-semantic-error h-11 px-5 text-base font-medium text-white transition-colors hover:bg-semantic-error/90 focus:outline-none focus-visible:ring-2 focus-visible:ring-semantic-error focus-visible:ring-offset-2 disabled:opacity-50"
          >
            {isDeletingAvatar ? 'Menghapus…' : 'Hapus Foto'}
          </button>
        </div>
      </Modal>
    </div>
  );
};

export default DoctorProfile;
