import { supabase, isSupabaseConfigured } from '@/lib/supabase';
import type { User } from '@supabase/supabase-js';

export interface EducationItem {
  id: string;
  institution: string;
  degree: string;
  fieldOfStudy: string;
  startYear?: string;
  endYear?: string;
  certifications?: string;
}

export interface ExperienceItem {
  id: string;
  institution: string;
  position: string;
  period: string;
  description?: string;
}

export interface DoctorProfileData {
  // Personal
  fullName: string;
  phone?: string;
  birthDate?: string; // YYYY-MM-DD
  city?: string;

  // Professional
  professionCategory?: string;
  academicTitle?: string;
  primarySpecialty?: string;
  subspecialty?: string;
  clinicalFocus?: string;
  hospital?: string;
  department?: string;
  clinicalRole?: string;
  yearsExperience?: string;
  practiceAddress?: string;
  strNumber?: string;
  isVerified?: boolean;

  // Biography
  bio?: string;

  // Dynamic Lists
  education: EducationItem[];
  experience: ExperienceItem[];

  // Metadata
  updatedAt?: string;
  avatarUrl?: string;

  // Role & Account Status (two-role system)
  role?: 'doctor' | 'admin';
  accountStatus?: 'pending' | 'approved' | 'rejected';
  approvalReason?: string | null;
}

/**
 * Maps raw database row into typed DoctorProfileData.
 */
function mapRowToProfile(row: Record<string, unknown>, fallbackUser: User): DoctorProfileData {
  const metadataProfile = (fallbackUser.user_metadata?.doctor_profile as Partial<DoctorProfileData>) || {};
  return {
    fullName: (typeof row.full_name === 'string' && row.full_name) || fallbackUser.user_metadata?.full_name || '',
    phone: typeof row.phone === 'string' ? row.phone : undefined,
    birthDate: typeof row.birth_date === 'string' ? row.birth_date : undefined,
    city: typeof row.city === 'string' ? row.city : undefined,
    professionCategory: typeof row.profession_category === 'string' ? row.profession_category : undefined,
    academicTitle: typeof row.academic_title === 'string' ? row.academic_title : undefined,
    primarySpecialty:
      (typeof row.primary_specialty === 'string' && row.primary_specialty) ||
      (fallbackUser.user_metadata?.primary_specialty as string) ||
      (fallbackUser.user_metadata?.specialty as string) ||
      metadataProfile.primarySpecialty ||
      undefined,
    subspecialty: typeof row.subspecialty === 'string' ? row.subspecialty : undefined,
    clinicalFocus: typeof row.clinical_focus === 'string' ? row.clinical_focus : undefined,
    hospital:
      (typeof row.hospital === 'string' && row.hospital) ||
      (fallbackUser.user_metadata?.hospital as string) ||
      (fallbackUser.user_metadata?.hospital_name as string) ||
      metadataProfile.hospital ||
      undefined,
    department: typeof row.department === 'string' ? row.department : undefined,
    clinicalRole: typeof row.clinical_role === 'string' ? row.clinical_role : undefined,
    yearsExperience: typeof row.years_experience === 'string' ? row.years_experience : undefined,
    practiceAddress: typeof row.practice_address === 'string' ? row.practice_address : undefined,
    strNumber: typeof row.str_number === 'string' ? row.str_number : undefined,
    isVerified: typeof row.is_verified === 'boolean' ? row.is_verified : false,
    bio: typeof row.bio === 'string' ? row.bio : undefined,
    education: Array.isArray(row.education) ? (row.education as EducationItem[]) : [],
    experience: Array.isArray(row.experience) ? (row.experience as ExperienceItem[]) : [],
    updatedAt: typeof row.updated_at === 'string' ? row.updated_at : undefined,
    avatarUrl: typeof row.avatar_url === 'string' ? row.avatar_url : undefined,
    role: (typeof row.role === 'string' && (row.role === 'doctor' || row.role === 'admin' ? row.role : 'doctor')) as 'doctor' | 'admin' | undefined,
    accountStatus: (typeof row.account_status === 'string' && (row.account_status === 'pending' || row.account_status === 'approved' || row.account_status === 'rejected' ? row.account_status : 'pending')) as 'pending' | 'approved' | 'rejected' | undefined,
    approvalReason: typeof row.rejection_reason === 'string' ? row.rejection_reason : null,
  };
}

/**
 * Loads doctor profile from Supabase.
 * Checks the `doctor_profiles` table first; if the table is not yet migrated,
 * falls back gracefully to `user.user_metadata.doctor_profile`.
 */
export async function fetchDoctorProfile(user: User): Promise<DoctorProfileData> {
  const metadataProfile = (user.user_metadata?.doctor_profile as Partial<DoctorProfileData>) || {};
  const defaultProfile: DoctorProfileData = {
    fullName: (user.user_metadata?.full_name as string) || metadataProfile.fullName || '',
    phone: metadataProfile.phone,
    birthDate: metadataProfile.birthDate,
    city: metadataProfile.city,
    professionCategory: metadataProfile.professionCategory,
    academicTitle: metadataProfile.academicTitle,
    primarySpecialty:
      metadataProfile.primarySpecialty ||
      (user.user_metadata?.primary_specialty as string) ||
      (user.user_metadata?.specialty as string) ||
      undefined,
    subspecialty: metadataProfile.subspecialty,
    clinicalFocus: metadataProfile.clinicalFocus,
    hospital:
      metadataProfile.hospital ||
      (user.user_metadata?.hospital as string) ||
      (user.user_metadata?.hospital_name as string) ||
      undefined,
    department: metadataProfile.department,
    clinicalRole: metadataProfile.clinicalRole,
    yearsExperience: metadataProfile.yearsExperience,
    practiceAddress: metadataProfile.practiceAddress,
    strNumber: metadataProfile.strNumber,
    isVerified: metadataProfile.isVerified ?? false,
    bio: metadataProfile.bio,
    education: metadataProfile.education || [],
    experience: metadataProfile.experience || [],
    updatedAt: metadataProfile.updatedAt,
    avatarUrl: metadataProfile.avatarUrl,
    role: metadataProfile.role || 'doctor',
    accountStatus: metadataProfile.accountStatus || 'pending',
  };

  if (!isSupabaseConfigured) {
    return defaultProfile;
  }

  try {
    const { data, error } = await supabase
      .from('doctor_profiles')
      .select('*')
      .eq('user_id', user.id)
      .maybeSingle();

    if (!error && data) {
      return mapRowToProfile(data as Record<string, unknown>, user);
    }

    return defaultProfile;
  } catch {
    return defaultProfile;
  }
}

/**
 * Validates doctor profile input before saving.
 */
export function validateProfileData(data: DoctorProfileData): { isValid: boolean; errors: Record<string, string> } {
  const errors: Record<string, string> = {};

  if (!data.fullName || data.fullName.trim().length === 0) {
    errors.fullName = 'Nama lengkap wajib diisi.';
  } else if (data.fullName.trim().length > 150) {
    errors.fullName = 'Nama lengkap maksimal 150 karakter.';
  }

  if (data.phone && data.phone.trim().length > 30) {
    errors.phone = 'Nomor telepon maksimal 30 karakter.';
  }

  if (data.bio && data.bio.length > 1000) {
    errors.bio = 'Biografi profesional maksimal 1000 karakter.';
  }

  if (data.strNumber && data.strNumber.trim().length > 50) {
    errors.strNumber = 'Nomor STR/izin praktik maksimal 50 karakter.';
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}

/**
 * Saves doctor profile with dual persistence:
 * 1. Attempts upsert to `public.doctor_profiles` table.
 * 2. Synchronizes with Supabase Auth `user_metadata` via `supabase.auth.updateUser`
 *    so data is guaranteed persistent across refreshes and logins even before table migration.
 *
 * Each step is tracked separately so the caller can distinguish between
 * Storage upload success, database upsert failure, and auth metadata failure.
 */
const AVATAR_BUCKET = 'profile-avatars';
const MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024; // 5 MB
const ALLOWED_AVATAR_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

function sanitizePathPart(part: string): string {
  return part.replace(/[^\w\-_.~]/g, '').slice(0, 128);
}

export async function uploadAvatar(
  user: User,
  file: File,
): Promise<{ url: string; error?: string }> {
  if (!isSupabaseConfigured) {
    return { url: '', error: 'Supabase belum dikonfigurasi.' };
  }
  if (!ALLOWED_AVATAR_MIME_TYPES.includes(file.type)) {
    return { url: '', error: 'Format file tidak didukung. Gunakan JPEG, PNG, atau WebP.' };
  }
  if (file.size > MAX_AVATAR_SIZE_BYTES) {
    return { url: '', error: 'Ukuran file melebihi batas 5 MB.' };
  }
  const ext = file.name.split('.').pop()?.toLowerCase() ?? 'jpg';
  // UUIDs contain only [a-f0-9-] which passes the safe-char filter unchanged.
  // Sanitizing prevents path-traversal characters like / \ space etc.
  const safeUserId = sanitizePathPart(user.id);
  const path = `${safeUserId}/profile.${ext}`;
  try {
    const { data: uploadData, error: uploadError } = await supabase.storage
      .from(AVATAR_BUCKET)
      .upload(path, file, { upsert: true });
    if (uploadError) {
      // Diagnostic: log enough to identify whether this is a Storage RLS error
      // or a database-level error. Do NOT log tokens or PII beyond the masked ID.
      console.warn('[uploadAvatar] Storage upload failed:', {
        bucket: AVATAR_BUCKET,
        path,
        mime: file.type,
        sizeBytes: file.size,
        userIdMasked: `${safeUserId.slice(0, 4)}…${safeUserId.slice(-4)}`,
        message: uploadError.message,
        code: (uploadError as unknown as Record<string, unknown>)?.code as string | undefined,
      });
      return { url: '', error: uploadError.message };
    }
    const { data: urlData } = supabase.storage.from(AVATAR_BUCKET).getPublicUrl(uploadData.path);
    return { url: urlData.publicUrl };
  } catch (err) {
    console.warn('[uploadAvatar] Unexpected error:', err instanceof Error ? err.message : String(err));
    return { url: '', error: err instanceof Error ? err.message : 'Upload gagal.' };
  }
}

export async function deleteAvatar(user: User): Promise<{ success: boolean; error?: string }> {
  if (!isSupabaseConfigured) return { success: false, error: 'Supabase belum dikonfigurasi.' };
  const safeId = sanitizePathPart(user.id);
  try {
    await supabase.storage.from(AVATAR_BUCKET).remove([
      `${safeId}/profile.jpg`,
      `${safeId}/profile.png`,
      `${safeId}/profile.webp`,
    ]);
    return { success: true };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Deletion failed.' };
  }
}

export async function saveDoctorProfile(
  user: User,
  data: DoctorProfileData
): Promise<{ data?: DoctorProfileData; error?: string }> {
  const validation = validateProfileData(data);
  if (!validation.isValid) {
    const firstError = Object.values(validation.errors)[0] || 'Validasi formulir gagal.';
    return { error: firstError };
  }

  const sanitized: DoctorProfileData = {
    ...data,
    fullName: data.fullName.trim(),
    phone: data.phone?.trim() || undefined,
    birthDate: data.birthDate || undefined,
    city: data.city?.trim() || undefined,
    professionCategory: data.professionCategory?.trim() || undefined,
    academicTitle: data.academicTitle?.trim() || undefined,
    primarySpecialty: data.primarySpecialty?.trim() || undefined,
    subspecialty: data.subspecialty?.trim() || undefined,
    clinicalFocus: data.clinicalFocus?.trim() || undefined,
    hospital: data.hospital?.trim() || undefined,
    department: data.department?.trim() || undefined,
    clinicalRole: data.clinicalRole?.trim() || undefined,
    yearsExperience: data.yearsExperience?.trim() || undefined,
    practiceAddress: data.practiceAddress?.trim() || undefined,
    strNumber: data.strNumber?.trim() || undefined,
    isVerified: data.isVerified ?? false,
    bio: data.bio?.trim() || undefined,
    education: data.education || [],
    experience: data.experience || [],
    updatedAt: new Date().toISOString(),
  };

  if (!isSupabaseConfigured) {
    return { data: sanitized };
  }

  // Track each persistence step separately so failures are reported precisely
  let dbUpsertError: string | null = null;
  let authMetaError: string | null = null;

  // 1. Upsert into `doctor_profiles` table
  // IMPORTANT: role and account_status are never included in the upsert
  // payload. These fields are managed exclusively by the backend admin API
  // (service-role) and must never be user-supplied.
  try {
    const dbPayload = {
      user_id: user.id,
      full_name: sanitized.fullName,
      phone: sanitized.phone ?? null,
      birth_date: sanitized.birthDate ?? null,
      city: sanitized.city ?? null,
      profession_category: sanitized.professionCategory ?? null,
      academic_title: sanitized.academicTitle ?? null,
      primary_specialty: sanitized.primarySpecialty ?? null,
      subspecialty: sanitized.subspecialty ?? null,
      clinical_focus: sanitized.clinicalFocus ?? null,
      hospital: sanitized.hospital ?? null,
      department: sanitized.department ?? null,
      clinical_role: sanitized.clinicalRole ?? null,
      years_experience: sanitized.yearsExperience ?? null,
      practice_address: sanitized.practiceAddress ?? null,
      str_number: sanitized.strNumber ?? null,
      is_verified: sanitized.isVerified ?? false,
      bio: sanitized.bio ?? null,
      education: sanitized.education,
      experience: sanitized.experience,
      updated_at: sanitized.updatedAt,
      avatar_url: sanitized.avatarUrl ?? null,
    };

    const { error: upsertError } = await supabase
      .from('doctor_profiles')
      .upsert(dbPayload, { onConflict: 'user_id' });

    if (upsertError) {
      // Diagnostic: log the actual Supabase error details for debugging
      console.warn('[saveDoctorProfile] doctor_profiles upsert failed:', upsertError.message);
      dbUpsertError = upsertError.message;
    }
  } catch (err) {
    dbUpsertError = err instanceof Error ? err.message : 'Database error';
    console.warn('[saveDoctorProfile] doctor_profiles upsert threw:', dbUpsertError);
  }

  // 2. Synchronize with Supabase Auth metadata for seamless cross-session persistence
  try {
    const { error: authError } = await supabase.auth.updateUser({
      data: {
        full_name: sanitized.fullName,
        doctor_profile: sanitized,
      },
    });

    if (authError) {
      // Diagnostic: log the actual Supabase auth error details for debugging
      console.warn('[saveDoctorProfile] auth.updateUser failed:', authError.message);
      authMetaError = authError.message;
    }
  } catch (err) {
    authMetaError = err instanceof Error ? err.message : 'Auth metadata error';
    console.warn('[saveDoctorProfile] auth.updateUser threw:', authMetaError);
  }

  // Return a precise error message indicating which step failed
  if (dbUpsertError) {
    const detail = authMetaError
      ? `Database simpan gagal (${dbUpsertError}). ${authMetaError}`
      : dbUpsertError;
    return { error: `Gagal menyimpan profil ke database: ${detail}` };
  }
  if (authMetaError) {
    // Database saved successfully but auth metadata sync failed — still return data
    // so the avatar is persisted in doctor_profiles; auth metadata is a fallback
    console.warn('[saveDoctorProfile] Profile saved to DB but auth metadata sync failed:', authMetaError);
    return { data: sanitized };
  }

  return { data: sanitized };
}
