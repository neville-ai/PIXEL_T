import { describe, it, expect, vi, beforeEach } from 'vitest';
import type { User } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabase';
import {
  validateProfileData,
  fetchDoctorProfile,
  saveDoctorProfile,
  type DoctorProfileData,
} from './profile';

vi.mock('@/lib/supabase', () => ({
  isSupabaseConfigured: true,
  supabase: {
    from: vi.fn(),
    auth: {
      updateUser: vi.fn(),
    },
  },
}));

function makeUser(overrides: Partial<User> = {}): User {
  return {
    id: 'user-uuid-1234',
    email: 'dr.neville@example.com',
    user_metadata: {
      full_name: 'Dr. Neville',
    },
    ...overrides,
  } as unknown as User;
}

function makeSampleProfile(): DoctorProfileData {
  return {
    fullName: 'Dr. Neville, Sp.PD-KGEH',
    phone: '+62 812 3456 7890',
    birthDate: '1985-05-20',
    city: 'Yogyakarta',
    professionCategory: 'Dokter Spesialis Penyakit Dalam',
    academicTitle: 'Sp.PD-KGEH',
    primarySpecialty: 'Gastroenterologi Hepatologi',
    subspecialty: 'Endoskopi Intervensi',
    clinicalFocus: 'Gastrointestinal Endoscopy & Colorectal Screening',
    hospital: 'RSUP Dr. Sardjito Yogyakarta',
    department: 'Instalasi Endoskopi Saluran Cerna',
    clinicalRole: 'Lead Endoscopist / Attending Physician',
    yearsExperience: '12',
    practiceAddress: 'Jl. Kesehatan No. 1, Sleman, DIY',
    strNumber: 'KKI-7829104',
    isVerified: true,
    bio: 'Dokter spesialis penyakit dalam konsultan gastroenterologi hepatologi.',
    education: [
      {
        id: 'edu-1',
        institution: 'Universitas Gadjah Mada',
        degree: 'Sp-2 (Konsultan)',
        fieldOfStudy: 'Gastroenterologi Hepatologi',
        startYear: '2018',
        endYear: '2021',
      },
    ],
    experience: [
      {
        id: 'exp-1',
        institution: 'RSUP Dr. Sardjito',
        position: 'Lead Endoscopist',
        period: '2021 - Sekarang',
        description: 'Tindakan kolonoskopi diagnostik dan terapeutik.',
      },
    ],
  };
}

describe('profile service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('validateProfileData', () => {
    it('rejects empty full name', () => {
      const invalid: DoctorProfileData = {
        fullName: '   ',
        education: [],
        experience: [],
      };
      const res = validateProfileData(invalid);
      expect(res.isValid).toBe(false);
      expect(res.errors.fullName).toBeDefined();
    });

    it('rejects bio longer than 1000 characters', () => {
      const longBio = 'A'.repeat(1005);
      const invalid: DoctorProfileData = {
        fullName: 'Dr. Test',
        bio: longBio,
        education: [],
        experience: [],
      };
      const res = validateProfileData(invalid);
      expect(res.isValid).toBe(false);
      expect(res.errors.bio).toContain('1000');
    });

    it('accepts a valid profile', () => {
      const valid = makeSampleProfile();
      const res = validateProfileData(valid);
      expect(res.isValid).toBe(true);
      expect(Object.keys(res.errors)).toHaveLength(0);
    });
  });

  describe('fetchDoctorProfile', () => {
    it('reads from Supabase doctor_profiles table when row exists', async () => {
      const mockedSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          maybeSingle: vi.fn().mockResolvedValue({
            data: {
              full_name: 'Dr. Database User',
              hospital: 'RS Sardjito',
              education: [],
              experience: [],
            },
            error: null,
          }),
        }),
      });
      vi.mocked(supabase.from).mockReturnValue({ select: mockedSelect } as any);

      const user = makeUser();
      const profile = await fetchDoctorProfile(user);

      expect(profile.fullName).toBe('Dr. Database User');
      expect(profile.hospital).toBe('RS Sardjito');
    });

    it('falls back to user_metadata when table returns empty or error', async () => {
      const mockedSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          maybeSingle: vi.fn().mockResolvedValue({
            data: null,
            error: { code: 'PGRST205', message: 'Table not found' },
          }),
        }),
      });
      vi.mocked(supabase.from).mockReturnValue({ select: mockedSelect } as any);

      const user = makeUser({
        user_metadata: {
          full_name: 'Dr. Neville',
          doctor_profile: {
            hospital: 'Klinik Metadata',
            education: [],
            experience: [],
          },
        },
      });

      const profile = await fetchDoctorProfile(user);
      expect(profile.fullName).toBe('Dr. Neville');
      expect(profile.hospital).toBe('Klinik Metadata');
    });

    it('populates hospital and primarySpecialty from registration user_metadata when table has no row', async () => {
      const mockedSingle = vi.fn().mockResolvedValue({
        data: null,
        error: { code: 'PGRST116', message: 'Row not found' },
      });
      const mockedSelect = vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: mockedSingle,
        }),
      });
      vi.mocked(supabase.from).mockReturnValue({ select: mockedSelect } as any);

      const user = makeUser({
        user_metadata: {
          full_name: 'Dr. Jane Smith',
          hospital_name: 'RSUP Prof. Dr. R. D. Kandou',
          specialty: 'Patologi Anatomi',
        },
      });

      const profile = await fetchDoctorProfile(user);
      expect(profile.fullName).toBe('Dr. Jane Smith');
      expect(profile.hospital).toBe('RSUP Prof. Dr. R. D. Kandou');
      expect(profile.primarySpecialty).toBe('Patologi Anatomi');
    });
  });

  describe('saveDoctorProfile', () => {
    it('returns validation error on invalid input without network calls', async () => {
      const user = makeUser();
      const result = await saveDoctorProfile(user, {
        fullName: '',
        education: [],
        experience: [],
      });

      expect(result.error).toBeDefined();
      expect(supabase.from).not.toHaveBeenCalled();
      expect(supabase.auth.updateUser).not.toHaveBeenCalled();
    });

    it('persists data using both table upsert and auth metadata update', async () => {
      const mockedUpsert = vi.fn().mockResolvedValue({ error: null });
      vi.mocked(supabase.from).mockReturnValue({ upsert: mockedUpsert } as any);
      vi.mocked(supabase.auth.updateUser).mockResolvedValue({ data: {} as any, error: null });

      const user = makeUser();
      const profileData = makeSampleProfile();

      const result = await saveDoctorProfile(user, profileData);

      expect(result.error).toBeUndefined();
      expect(result.data).toBeDefined();
      expect(mockedUpsert).toHaveBeenCalledWith(
        expect.objectContaining({
          user_id: user.id,
          full_name: profileData.fullName,
        }),
        { onConflict: 'user_id' }
      );
      expect(supabase.auth.updateUser).toHaveBeenCalledWith(
        expect.objectContaining({
          data: expect.objectContaining({
            full_name: profileData.fullName,
            doctor_profile: expect.any(Object),
          }),
        })
      );
    });

    it('includes avatar_url in the upsert payload when avatarUrl is present', async () => {
      const mockedUpsert = vi.fn().mockResolvedValue({ error: null });
      vi.mocked(supabase.from).mockReturnValue({ upsert: mockedUpsert } as any);
      vi.mocked(supabase.auth.updateUser).mockResolvedValue({ data: {} as any, error: null });

      const user = makeUser();
      const profileData = { ...makeSampleProfile(), avatarUrl: 'https://example.com/avatar.jpg' };

      const result = await saveDoctorProfile(user, profileData);

      expect(result.error).toBeUndefined();
      expect(mockedUpsert).toHaveBeenCalledWith(
        expect.objectContaining({ avatar_url: 'https://example.com/avatar.jpg' }),
        { onConflict: 'user_id' }
      );
    });

    it('includes avatar_url as null when avatarUrl is not provided', async () => {
      const mockedUpsert = vi.fn().mockResolvedValue({ error: null });
      vi.mocked(supabase.from).mockReturnValue({ upsert: mockedUpsert } as any);
      vi.mocked(supabase.auth.updateUser).mockResolvedValue({ data: {} as any, error: null });

      const user = makeUser();
      const profileData = makeSampleProfile(); // no avatarUrl

      const result = await saveDoctorProfile(user, profileData);

      expect(result.error).toBeUndefined();
      expect(mockedUpsert).toHaveBeenCalledWith(
        expect.objectContaining({ avatar_url: null }),
        { onConflict: 'user_id' }
      );
    });

    it('returns error when upsert fails even if auth metadata sync succeeds', async () => {
      const mockedUpsert = vi.fn().mockResolvedValue({
        error: new Error('new row violates row-level security policy'),
      });
      vi.mocked(supabase.from).mockReturnValue({ upsert: mockedUpsert } as any);
      vi.mocked(supabase.auth.updateUser).mockResolvedValue({ data: {} as any, error: null });

      const user = makeUser();
      const profileData = makeSampleProfile();

      const result = await saveDoctorProfile(user, profileData);

      // DB failure must surface as an error, not silently return success
      expect(result.error).toBeDefined();
      expect(result.error).toContain('Gagal menyimpan profil ke database');
    });

    it('returns error when both upsert and auth metadata sync fail', async () => {
      const mockedUpsert = vi.fn().mockResolvedValue({
        error: new Error('upsert error'),
      });
      vi.mocked(supabase.from).mockReturnValue({ upsert: mockedUpsert } as any);
      vi.mocked(supabase.auth.updateUser).mockResolvedValue({
        data: { user: null } as any,
        error: { message: 'auth error' } as any,
      } as any);

      const user = makeUser();
      const profileData = makeSampleProfile();

      const result = await saveDoctorProfile(user, profileData);

      expect(result.error).toBeDefined();
      expect(result.error).toContain('Database simpan gagal');
    });

    it('returns data when only auth metadata sync fails but upsert succeeds', async () => {
      const mockedUpsert = vi.fn().mockResolvedValue({ error: null });
      vi.mocked(supabase.from).mockReturnValue({ upsert: mockedUpsert } as any);
      vi.mocked(supabase.auth.updateUser).mockResolvedValue({
        data: { user: null } as any,
        error: { message: 'auth metadata error' } as any,
      } as any);

      const user = makeUser();
      const profileData = makeSampleProfile();

      const result = await saveDoctorProfile(user, profileData);

      // DB saved successfully; auth metadata failure is a warning, not a hard error
      expect(result.error).toBeUndefined();
      expect(result.data).toBeDefined();
      expect(result.data?.avatarUrl).toBeUndefined();
    });
  });
});
