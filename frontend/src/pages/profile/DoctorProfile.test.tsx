import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { supabase } from '@/lib/supabase';
import { listHistory, type HistoryList } from '@/services/analysis';
import * as profileService from '@/services/profile';
import { DoctorProfile } from './DoctorProfile';

vi.mock('@/context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/services/analysis', () => ({
  listHistory: vi.fn(),
}));

vi.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: vi.fn(),
    },
  },
  isSupabaseConfigured: true,
}));

const mockedGetSession = vi.mocked(supabase.auth.getSession);

type AuthUser = NonNullable<ReturnType<typeof useAuth>['user']>;

const mockedUseAuth = vi.mocked(useAuth);
const mockedListHistory = vi.mocked(listHistory);

function makeUser(overrides: Partial<AuthUser> = {}): AuthUser {
  return {
    id: 'usr_9f82a1e9-4c2b-47e1-b841-3b7c89d201a4',
    email: 'nevilleawuy@gmail.com',
    created_at: '2025-01-14T08:30:00Z',
    user_metadata: { full_name: 'Dr. Neville' },
    ...overrides,
  } as unknown as AuthUser;
}

function makeList(): HistoryList {
  return {
    items: [
      {
        id: 'analysis-1',
        created_at: '2026-10-06T14:15:00Z',
        status: 'completed',
        original_filename: 'COLON_CASE_2026_094.png',
        thumbnail_url: 'https://storage.example/signed/thumb-1.png',
        segmentation_status: 'detected',
      },
      {
        id: 'analysis-2',
        created_at: '2026-10-05T11:20:00Z',
        status: 'completed',
        original_filename: 'SIGMOID_FRAME_0182.jpeg',
        thumbnail_url: null,
        segmentation_status: 'not_detected',
      },
      {
        id: 'analysis-3',
        created_at: '2026-10-04T09:45:00Z',
        status: 'processing',
        original_filename: 'ENDOSCOPY_INGEST_884.dcm',
        thumbnail_url: null,
      },
      {
        id: 'analysis-4',
        created_at: '2026-10-03T08:00:00Z',
        status: 'failed',
        original_filename: 'patient_scan_validation_check_09.png',
        thumbnail_url: null,
      },
      {
        id: 'analysis-5',
        created_at: '2026-10-02T08:00:00Z',
        status: 'completed',
        original_filename: 'extra_record.png',
        thumbnail_url: null,
      },
    ],
  };
}

function makeSampleDoctorProfile(): profileService.DoctorProfileData {
  return {
    fullName: 'Dr. Neville',
    academicTitle: 'Sp.PD-KGEH',
    phone: '+62 812 3456 7890',
    birthDate: '1985-05-20',
    city: 'Yogyakarta',
    professionCategory: 'Dokter Spesialis Penyakit Dalam',
    primarySpecialty: 'Gastroenterologi Hepatologi',
    subspecialty: 'Endoskopi Saluran Cerna',
    clinicalFocus: 'Gastrointestinal Endoscopy & Colorectal Screening',
    hospital: 'RSUP Dr. Sardjito Yogyakarta',
    department: 'Instalasi Endoskopi Saluran Cerna',
    clinicalRole: 'Lead Endoscopist / Attending Physician',
    yearsExperience: '12',
    practiceAddress: 'Jl. Kesehatan No. 1, Yogyakarta',
    strNumber: 'KKI-7829104',
    isVerified: false,
    bio: 'Dokter spesialis penyakit dalam konsultan gastroenterologi hepatologi.',
    education: [
      {
        id: 'edu-1',
        institution: 'Universitas Gadjah Mada',
        degree: 'Sp-2 (Konsultan)',
        fieldOfStudy: 'Gastroenterologi Hepatologi',
        startYear: '2018',
        endYear: '2021',
        certifications: 'Advanced Endoscopy Fellowship',
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

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/profile']}>
      <Routes>
        <Route path="/profile" element={<DoctorProfile />} />
        <Route path="/analysis/new" element={<div>NEW ANALYSIS PAGE</div>} />
        <Route path="/analysis/:id" element={<div>ANALYSIS RESULT PAGE</div>} />
        <Route path="/history" element={<div>HISTORY PAGE</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  mockedUseAuth.mockReturnValue({
    user: makeUser(),
    session: null,
    loading: false,
    role: 'doctor',
    accountStatus: 'approved',
    signIn: vi.fn(),
    signUp: vi.fn(),
    signOut: vi.fn(),
  } as unknown as ReturnType<typeof useAuth>);
  mockedListHistory.mockReset();
  vi.spyOn(profileService, 'fetchDoctorProfile').mockResolvedValue({
    fullName: 'Dr. Neville',
    education: [],
    experience: [],
  });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('DoctorProfile — Account & Initial Loading', () => {
  it('loads profile based on authenticated user and displays auth session data', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    renderPage();

    expect(await screen.findAllByText('Dr. Neville')).toHaveLength(2);
    expect(screen.getAllByText('nevilleawuy@gmail.com')).toHaveLength(2);
  });

  it('falls back to "Not available" when user metadata has no name', async () => {
    mockedUseAuth.mockReturnValue({
      user: makeUser({ user_metadata: {} }),
      session: null,
      loading: false,
      role: 'doctor',
      accountStatus: 'approved',
      signIn: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
    } as unknown as ReturnType<typeof useAuth>);
    mockedListHistory.mockResolvedValue({ items: [] });
    vi.spyOn(profileService, 'fetchDoctorProfile').mockResolvedValue({
      fullName: '',
      education: [],
      experience: [],
    });

    renderPage();

    expect(await screen.findAllByText('nevilleawuy@gmail.com')).toHaveLength(3);
    expect(screen.getAllByText('Not available').length).toBeGreaterThanOrEqual(1);
  });
});

describe('DoctorProfile — Rendering Populated Profile', () => {
  it('renders professional details, hospital affiliation, and specialization', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    const fullProfile = makeSampleDoctorProfile();
    vi.spyOn(profileService, 'fetchDoctorProfile').mockResolvedValue(fullProfile);

    renderPage();

    expect(await screen.findByText('Dr. Neville, Sp.PD-KGEH')).toBeTruthy();
    expect(screen.getByText('RSUP Dr. Sardjito Yogyakarta')).toBeTruthy();
    expect(screen.getByText('Lead Endoscopist / Attending Physician')).toBeTruthy();
    expect(screen.getByText(/Gastroenterologi Hepatologi/)).toBeTruthy();
    // Sections D, E, F and KKI/STR are hidden from display
    expect(screen.queryByText('KKI-7829104')).toBeNull();
    expect(screen.queryByText('Universitas Gadjah Mada')).toBeNull();
    expect(screen.queryByText('Lead Endoscopist')).toBeNull();
    expect(screen.queryByText('Dokter spesialis penyakit dalam konsultan gastroenterologi hepatologi.')).toBeNull();
  });
});

describe('DoctorProfile — Editing & Persistence', () => {
  it('opens section-specific edit modals for each section', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    const fullProfile = makeSampleDoctorProfile();
    vi.spyOn(profileService, 'fetchDoctorProfile').mockResolvedValue(fullProfile);
    const saveSpy = vi.spyOn(profileService, 'saveDoctorProfile').mockResolvedValue({
      data: { ...fullProfile, professionCategory: 'Dokter Spesialis Baru' },
    });

    renderPage();

    // 1. Edit Clinical Details (Section A)
    const editClinicalBtn = await screen.findByRole('button', { name: 'Edit Clinical Details' });
    fireEvent.click(editClinicalBtn);
    expect(await screen.findByRole('heading', { name: 'Edit Clinical Details' })).toBeTruthy();
    // Section A fields should be present
    expect(screen.getByPlaceholderText('e.g. Dokter Spesialis Penyakit Dalam')).toBeTruthy();
    expect(screen.getByPlaceholderText('e.g. Gastroenterologi Hepatologi')).toBeTruthy();
    // Section B fields should NOT be present
    expect(screen.queryByPlaceholderText('e.g. Dr. Neville')).toBeNull();
    expect(screen.queryByPlaceholderText('e.g. +62 812 3456 7890')).toBeNull();
    // Section C fields should NOT be present
    expect(screen.queryByPlaceholderText('e.g. RSUP Dr. Sardjito Yogyakarta')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    // 2. Edit Personal Information (Section B)
    const editPersonalBtn = await screen.findByRole('button', { name: 'Edit Profile' });
    fireEvent.click(editPersonalBtn);
    expect(await screen.findByRole('heading', { name: 'Edit Personal Information' })).toBeTruthy();
    expect(screen.getByPlaceholderText('e.g. Dr. Neville')).toBeTruthy();
    expect(screen.getByPlaceholderText('e.g. +62 812 3456 7890')).toBeTruthy();
    // Section A fields should NOT be present
    expect(screen.queryByPlaceholderText('e.g. Dokter Spesialis Penyakit Dalam')).toBeNull();
    // Section C fields should NOT be present
    expect(screen.queryByPlaceholderText('e.g. RSUP Dr. Sardjito Yogyakarta')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    // 3. Edit Affiliation (Section C)
    const editAffiliationBtn = await screen.findByRole('button', { name: 'Edit Affiliation' });
    fireEvent.click(editAffiliationBtn);
    expect(await screen.findByRole('heading', { name: 'Edit Hospital Affiliation' })).toBeTruthy();
    expect(screen.getByPlaceholderText('e.g. RSUP Dr. Sardjito Yogyakarta')).toBeTruthy();
    expect(screen.getByPlaceholderText('e.g. Instalasi Endoskopi')).toBeTruthy();
    // Section A fields should NOT be present
    expect(screen.queryByPlaceholderText('e.g. Dokter Spesialis Penyakit Dalam')).toBeNull();
    // Section B fields should NOT be present
    expect(screen.queryByPlaceholderText('e.g. Dr. Neville')).toBeNull();
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    // Save was never called during cancel
    expect(saveSpy).not.toHaveBeenCalled();
  });

  it('saves Section A changes without affecting other sections', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    const initialProfile = makeSampleDoctorProfile();
    vi.spyOn(profileService, 'fetchDoctorProfile').mockResolvedValue(initialProfile);
    const saveSpy = vi.spyOn(profileService, 'saveDoctorProfile').mockResolvedValue({
      data: { ...initialProfile, professionCategory: 'Dokter Spesialis Baru' },
    });

    renderPage();

    const editClinicalBtn = await screen.findByRole('button', { name: 'Edit Clinical Details' });
    fireEvent.click(editClinicalBtn);

    const professionInput = screen.getByPlaceholderText('e.g. Dokter Spesialis Penyakit Dalam');
    fireEvent.change(professionInput, { target: { value: 'Dokter Spesialis Baru' } });

    const saveBtn = screen.getByRole('button', { name: 'Save Changes' });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(saveSpy).toHaveBeenCalledTimes(1);
      const callArgs = saveSpy.mock.calls[0];
      expect(callArgs[1].professionCategory).toBe('Dokter Spesialis Baru');
      expect(callArgs[1].fullName).toBe('Dr. Neville');
      expect(callArgs[1].hospital).toBe('RSUP Dr. Sardjito Yogyakarta');
    });
  });

  it('saves Section B changes without affecting other sections', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    const initialProfile = makeSampleDoctorProfile();
    vi.spyOn(profileService, 'fetchDoctorProfile').mockResolvedValue(initialProfile);
    const saveSpy = vi.spyOn(profileService, 'saveDoctorProfile').mockResolvedValue({
      data: { ...initialProfile, fullName: 'Dr. Baru' },
    });

    renderPage();

    const editPersonalBtn = await screen.findByRole('button', { name: 'Edit Profile' });
    fireEvent.click(editPersonalBtn);

    const nameInput = screen.getByPlaceholderText('e.g. Dr. Neville');
    fireEvent.change(nameInput, { target: { value: 'Dr. Baru' } });

    const saveBtn = screen.getByRole('button', { name: 'Save Changes' });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(saveSpy).toHaveBeenCalledTimes(1);
      const callArgs = saveSpy.mock.calls[0];
      expect(callArgs[1].fullName).toBe('Dr. Baru');
      expect(callArgs[1].professionCategory).toBe('Dokter Spesialis Penyakit Dalam');
      expect(callArgs[1].hospital).toBe('RSUP Dr. Sardjito Yogyakarta');
    });
  });

  it('saves Section C changes without affecting other sections', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    const initialProfile = makeSampleDoctorProfile();
    vi.spyOn(profileService, 'fetchDoctorProfile').mockResolvedValue(initialProfile);
    const saveSpy = vi.spyOn(profileService, 'saveDoctorProfile').mockResolvedValue({
      data: { ...initialProfile, hospital: 'RS Baru' },
    });

    renderPage();

    const editAffiliationBtn = await screen.findByRole('button', { name: 'Edit Affiliation' });
    fireEvent.click(editAffiliationBtn);

    const hospitalInput = screen.getByPlaceholderText('e.g. RSUP Dr. Sardjito Yogyakarta');
    fireEvent.change(hospitalInput, { target: { value: 'RS Baru' } });

    const saveBtn = screen.getByRole('button', { name: 'Save Changes' });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(saveSpy).toHaveBeenCalledTimes(1);
      const callArgs = saveSpy.mock.calls[0];
      expect(callArgs[1].hospital).toBe('RS Baru');
      expect(callArgs[1].fullName).toBe('Dr. Neville');
      expect(callArgs[1].professionCategory).toBe('Dokter Spesialis Penyakit Dalam');
    });
  });

  it('section edit buttons do not trigger unrelated section saves', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    const fullProfile = makeSampleDoctorProfile();
    vi.spyOn(profileService, 'fetchDoctorProfile').mockResolvedValue(fullProfile);
    const saveSpy = vi.spyOn(profileService, 'saveDoctorProfile').mockResolvedValue({
      data: fullProfile,
    });

    renderPage();

    // Open Section A modal, type in a field, cancel
    const editClinicalBtn = await screen.findByRole('button', { name: 'Edit Clinical Details' });
    fireEvent.click(editClinicalBtn);
    const professionInput = screen.getByPlaceholderText('e.g. Dokter Spesialis Penyakit Dalam');
    fireEvent.change(professionInput, { target: { value: 'Changed Value' } });
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(saveSpy).not.toHaveBeenCalled();
  });
});

describe('DoctorProfile — Real Activity Stats & Recent Analyses', () => {
  it('computes stats honestly from listHistory without fabricated figures', async () => {
    mockedListHistory.mockResolvedValue(makeList());
    renderPage();

    expect(await screen.findByText('COLON_CASE_2026_094.png')).toBeTruthy();

    const stats = screen.getByText('Total Records').closest('div');
    expect(stats).toBeTruthy();

    const cardValues = Array.from(
      screen.getByText('Total Records').parentElement!.parentElement!.querySelectorAll('span'),
    ).map((node) => node.textContent);

    expect(cardValues).toContain('5'); // Total
    expect(cardValues).toContain('3'); // Completed
    expect(cardValues).toContain('1'); // Processing
    expect(cardValues).toContain('1'); // Failed
  });

  it('renders at most 3 recent records with links to /analysis/:id', async () => {
    mockedListHistory.mockResolvedValue(makeList());
    renderPage();

    expect(await screen.findByText('COLON_CASE_2026_094.png')).toBeTruthy();
    expect(screen.getByText('SIGMOID_FRAME_0182.jpeg')).toBeTruthy();
    expect(screen.getByText('ENDOSCOPY_INGEST_884.dcm')).toBeTruthy();

    // 4th and 5th items not shown (capped at 3)
    expect(screen.queryByText('patient_scan_validation_check_09.png')).toBeNull();

    const links = await screen.findAllByRole('link', { name: /View Result/i });
    expect(links[0].getAttribute('href')).toBe('/analysis/analysis-1');
  });

  it('shows empty state when user has no analyses yet', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    renderPage();

    expect(await screen.findByText('No recent analyses yet')).toBeTruthy();
  });

  it('shows error state with retry on network failure', async () => {
    mockedListHistory.mockRejectedValueOnce(new Error('Koneksi terputus.'));
    mockedListHistory.mockResolvedValueOnce(makeList());
    renderPage();

    expect(await screen.findByText('Koneksi terputus.')).toBeTruthy();
    fireEvent.click(screen.getByText('Coba Lagi'));
    expect(await screen.findByText('COLON_CASE_2026_094.png')).toBeTruthy();
  });
});

describe('DoctorProfile — A11y & Navigation', () => {
  it('EmptyState CTA button navigates cleanly without interactive nesting', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    const { container } = renderPage();

    const cta = await screen.findByRole('button', { name: 'Start New Analysis' });
    expect(container.querySelector('a button, button a, a a, button button')).toBeNull();

    fireEvent.click(cta);
    expect(await screen.findByText('NEW ANALYSIS PAGE')).toBeTruthy();
  });

  it('retains focus and keeps modal open when typing consecutive characters into professional fields', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    vi.spyOn(profileService, 'fetchDoctorProfile').mockResolvedValue(makeSampleDoctorProfile());
    renderPage();

    const editBtn = await screen.findByRole('button', { name: 'Edit Clinical Details' });
    fireEvent.click(editBtn);

    expect(await screen.findByRole('heading', { name: 'Edit Clinical Details' })).toBeTruthy();

    const professionInput = screen.getByPlaceholderText('e.g. Dokter Spesialis Penyakit Dalam');
    const closeBtn = screen.getByRole('button', { name: 'Close modal' });

    professionInput.focus();
    expect(document.activeElement).toBe(professionInput);

    const sequence = ['D', 'Dr', 'Dr.', 'Dr. ', 'Dr. J', 'Dr. Jane'];
    for (const val of sequence) {
      fireEvent.change(professionInput, { target: { value: val } });
      expect(screen.getByRole('heading', { name: 'Edit Clinical Details' })).toBeTruthy();
      expect(document.activeElement).not.toBe(closeBtn);
    }
    expect((professionInput as HTMLInputElement).value).toBe('Dr. Jane');

    // Type into hospital input (Section C modal)
    fireEvent.click(closeBtn);
    const editAffiliationBtn = await screen.findByRole('button', { name: 'Edit Affiliation' });
    fireEvent.click(editAffiliationBtn);
    expect(await screen.findByRole('heading', { name: 'Edit Hospital Affiliation' })).toBeTruthy();

    const hospitalInput = screen.getByPlaceholderText('e.g. RSUP Dr. Sardjito Yogyakarta');
    hospitalInput.focus();
    expect(document.activeElement).toBe(hospitalInput);

    for (const val of ['R', 'RS', 'RSU', 'RSUP', 'RSUP D', 'RSUP Dr. S']) {
      fireEvent.change(hospitalInput, { target: { value: val } });
      expect(screen.getByRole('heading', { name: 'Edit Hospital Affiliation' })).toBeTruthy();
      expect(document.activeElement).not.toBe(closeBtn);
    }
    expect((hospitalInput as HTMLInputElement).value).toBe('RSUP Dr. S');
  });
});

describe('DoctorProfile — Avatar Upload & Delete Confirmation', () => {
  const mockUploadAvatar = vi.fn<typeof profileService.uploadAvatar>();
  const mockDeleteAvatar = vi.fn<typeof profileService.deleteAvatar>();
  const mockSaveDoctorProfile = vi.fn<typeof profileService.saveDoctorProfile>();
  const mockFetchDoctorProfile = vi.fn<typeof profileService.fetchDoctorProfile>();

  function session_ok() {
    mockedGetSession.mockResolvedValue({
      data: { session: { access_token: 'test-token' } },
      error: null,
    } as never);
  }

  beforeEach(() => {
    mockUploadAvatar.mockReset();
    mockDeleteAvatar.mockReset();
    mockSaveDoctorProfile.mockReset();
    mockFetchDoctorProfile.mockReset();
    vi.spyOn(profileService, 'uploadAvatar').mockImplementation(mockUploadAvatar);
    vi.spyOn(profileService, 'deleteAvatar').mockImplementation(mockDeleteAvatar);
    vi.spyOn(profileService, 'saveDoctorProfile').mockImplementation(mockSaveDoctorProfile);
    vi.spyOn(profileService, 'fetchDoctorProfile').mockImplementation(mockFetchDoctorProfile);
    session_ok();
  });

  it('shows Hapus Foto button only when avatar URL is present', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    // No avatar
    mockFetchDoctorProfile.mockResolvedValue(makeSampleDoctorProfile());
    renderPage();
    await screen.findByText('Loading Doctor Profile');
    expect(screen.queryByText('Hapus Foto')).toBeNull();

    // With avatar
    mockFetchDoctorProfile.mockResolvedValue(
      { ...makeSampleDoctorProfile(), avatarUrl: 'https://example.com/avatar.jpg' },
    );
    renderPage();
    expect(await screen.findByText('Hapus Foto')).toBeTruthy();
  });

  it('opens delete confirmation modal when clicking Hapus Foto', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    mockFetchDoctorProfile.mockResolvedValue(
      { ...makeSampleDoctorProfile(), avatarUrl: 'https://example.com/avatar.jpg' },
    );
    renderPage();

    fireEvent.click(await screen.findByText('Hapus Foto'));
    expect(await screen.findByText('Hapus Foto Profil?')).toBeTruthy();
    expect(screen.getByText(/Apakah Anda yakin ingin menghapus foto profil/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Batal' })).toBeTruthy();
    // Two "Hapus Foto" buttons exist: trigger (index 0) and modal confirm (index 1)
    expect(screen.getAllByRole('button', { name: 'Hapus Foto' }).length).toBe(2);
  });

  it('cancel button closes modal without calling delete or save', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    mockFetchDoctorProfile.mockResolvedValue(
      { ...makeSampleDoctorProfile(), avatarUrl: 'https://example.com/avatar.jpg' },
    );
    renderPage();

    fireEvent.click(await screen.findByText('Hapus Foto'));
    expect(await screen.findByText('Hapus Foto Profil?')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Batal' }));
    expect(screen.queryByText('Hapus Foto Profil?')).toBeNull();
    expect(mockDeleteAvatar).not.toHaveBeenCalled();
    expect(mockSaveDoctorProfile).not.toHaveBeenCalled();
  });

  it('confirming delete calls deleteAvatar then saveDoctorProfile with removed avatarUrl', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    mockDeleteAvatar.mockResolvedValue({ success: true });
    mockSaveDoctorProfile.mockResolvedValue({ data: makeSampleDoctorProfile() });
    mockFetchDoctorProfile.mockResolvedValue(
      { ...makeSampleDoctorProfile(), avatarUrl: 'https://example.com/avatar.jpg' },
    );
    renderPage();

    fireEvent.click(await screen.findByText('Hapus Foto'));
    expect(await screen.findByText('Hapus Foto Profil?')).toBeTruthy();

    const deleteButtons = screen.getAllByRole('button', { name: 'Hapus Foto' });
    // [0] = page trigger, [1] = modal confirm button
    fireEvent.click(deleteButtons[1]);
    await waitFor(() => {
      expect(mockDeleteAvatar).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(mockSaveDoctorProfile).toHaveBeenCalledTimes(1);
    });

    const savedData = mockSaveDoctorProfile.mock.calls[0][1];
    expect(savedData.avatarUrl).toBeUndefined();

    // Modal should close after successful deletion
    await waitFor(() => {
      expect(screen.queryByText('Hapus Foto Profil?')).toBeNull();
    });
  });

  it('shows error when deleteAvatar fails', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    mockDeleteAvatar.mockResolvedValue({ success: false, error: 'RLS policy violation.' });
    mockFetchDoctorProfile.mockResolvedValue(
      { ...makeSampleDoctorProfile(), avatarUrl: 'https://example.com/avatar.jpg' },
    );
    renderPage();

    fireEvent.click(await screen.findByText('Hapus Foto'));
    expect(await screen.findByText('Hapus Foto Profil?')).toBeTruthy();

    const deleteButtons = screen.getAllByRole('button', { name: 'Hapus Foto' });
    fireEvent.click(deleteButtons[1]);
    await waitFor(() => {
      expect(screen.getByText('RLS policy violation.')).toBeTruthy();
    });

    // Modal stays open on error so user can retry
    expect(screen.queryByText('Hapus Foto Profil?')).toBeTruthy();
  });

  it('uploading avatar updates local state and calls saveDoctorProfile with new URL', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    const newUrl = 'https://example.com/new-avatar.webp';
    mockUploadAvatar.mockResolvedValue({ url: newUrl });
    mockSaveDoctorProfile.mockResolvedValue({ data: makeSampleDoctorProfile() });
    mockFetchDoctorProfile.mockResolvedValue(
      { ...makeSampleDoctorProfile(), avatarUrl: undefined },
    );
    renderPage();

    const input = await screen.findByLabelText('Tambah foto profil');
    const file = new File(['dummy'], 'photo.webp', { type: 'image/webp' });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(mockUploadAvatar).toHaveBeenCalledTimes(1);
    });
    await waitFor(() => {
      expect(mockSaveDoctorProfile).toHaveBeenCalledTimes(1);
    });

    const savedData = mockSaveDoctorProfile.mock.calls[0][1];
    expect(savedData.avatarUrl).toBe(newUrl);
  });

  it('upload error sets avatarError and does not call saveDoctorProfile', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    mockUploadAvatar.mockResolvedValue({ url: '', error: 'File too large.' });
    mockFetchDoctorProfile.mockResolvedValue(
      { ...makeSampleDoctorProfile(), avatarUrl: undefined },
    );
    renderPage();

    const input = await screen.findByLabelText('Tambah foto profil');
    const file = new File(['dummy'], 'photo.jpg', { type: 'image/jpeg' });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText('File too large.')).toBeTruthy();
    });
    expect(mockSaveDoctorProfile).not.toHaveBeenCalled();
  });

  it('upload succeeds but saveDoctorProfile error shows avatarError without updating local state', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    const newUrl = 'https://example.com/new-avatar.webp';
    mockUploadAvatar.mockResolvedValue({ url: newUrl });
    mockSaveDoctorProfile.mockResolvedValue({ error: 'new row violates row-level security policy' });
    mockFetchDoctorProfile.mockResolvedValue(
      { ...makeSampleDoctorProfile(), avatarUrl: undefined },
    );
    renderPage();

    const input = await screen.findByLabelText('Tambah foto profil');
    const file = new File(['dummy'], 'photo.webp', { type: 'image/webp' });
    fireEvent.change(input, { target: { files: [file] } });

    // The error should be surfaced since saveDoctorProfile failed
    await waitFor(() => {
      expect(screen.getByText(/new row violates row-level security policy/)).toBeTruthy();
    });
    // Avatar should NOT be shown (local state not updated)
    expect(screen.queryByAltText(/avatar/)).toBeNull();
    // Save was called with the new URL
    expect(mockSaveDoctorProfile).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ avatarUrl: newUrl }),
    );
  });

  it('upload is blocked when no active session and shows authentication error', async () => {
    mockedListHistory.mockResolvedValue({ items: [] });
    mockedGetSession.mockResolvedValue({ data: { session: null }, error: null } as never);
    mockFetchDoctorProfile.mockResolvedValue(
      { ...makeSampleDoctorProfile(), avatarUrl: undefined },
    );
    renderPage();

    const input = await screen.findByLabelText('Tambah foto profil');
    const file = new File(['dummy'], 'photo.jpg', { type: 'image/jpeg' });
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/Sesi autentikasi tidak ditemukan/)).toBeTruthy();
    });
    // Upload and save must not be called
    expect(mockUploadAvatar).not.toHaveBeenCalled();
    expect(mockSaveDoctorProfile).not.toHaveBeenCalled();
  });
});
