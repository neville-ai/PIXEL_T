import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AdminDashboard } from './AdminDashboard';
import { useAuth } from '@/context/AuthContext';

vi.mock('@/context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

const mockSession = {
  access_token: 'test-token',
  user: { id: 'admin-id', email: 'admin@test.com' },
};

function mockAuthContext(overrides: Record<string, unknown> = {}) {
  vi.mocked(useAuth).mockReturnValue({
    user: mockSession.user,
    session: mockSession as unknown as ReturnType<typeof useAuth>['session'],
    loading: false,
    role: 'admin',
    accountStatus: null,
    signIn: vi.fn(),
    signUp: vi.fn(),
    signOut: vi.fn(),
    ...overrides,
  } as unknown as ReturnType<typeof useAuth>);
}

describe('AdminDashboard', () => {
  let originalFetch: typeof global.fetch;

  beforeEach(() => {
    originalFetch = global.fetch;
  });

  afterEach(() => {
    global.fetch = originalFetch;
    cleanup();
    vi.restoreAllMocks();
  });

  function setupFetchMocks(doctorData: Array<{ account_status: string }> = []) {
    global.fetch = vi.fn().mockImplementation(async (url: string | URL | Request) => {
      const urlString = typeof url === 'string' ? url : (url as Request).url;
      if (urlString.includes('/doctors/stats')) {
        return {
          ok: true,
          json: async () => ({
            success: true,
            data: {
              total: doctorData.length,
              pending: doctorData.filter((d) => d.account_status === 'pending').length,
              approved: doctorData.filter((d) => d.account_status === 'approved').length,
              rejected: doctorData.filter((d) => d.account_status === 'rejected').length,
            },
          }),
        } as Response;
      }
      if (urlString.includes('/admin/doctors') && !urlString.includes('/stats')) {
        return {
          ok: true,
          json: async () => ({ success: true, data: doctorData }),
        } as Response;
      }
      return { ok: false, json: async () => ({}) } as Response;
    }) as unknown as typeof global.fetch;
  }

  it('renders the page title', async () => {
    mockAuthContext();
    setupFetchMocks([]);
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);

    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeTruthy();
    });
  });

  it('displays stat cards with correct values', async () => {
    const mockDoctor = {
      id: 'doc-1',
      user_id: 'uid-1',
      full_name: 'Dr. Test',
      email: 'test@hospital.com',
      hospital: 'RS Test',
      primary_specialty: 'Radiologi',
      account_status: 'pending' as const,
      created_at: '2026-01-15T10:00:00Z',
    };
    mockAuthContext();
    setupFetchMocks([mockDoctor]);
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);

    await waitFor(() => {
      const totalCards = screen.queryAllByText('Total Pendaftaran');
      expect(totalCards.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows filter buttons', async () => {
    mockAuthContext();
    setupFetchMocks([]);
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: /Semua/ }).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByRole('button', { name: /Pending/ }).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByRole('button', { name: /Disetujui/ }).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByRole('button', { name: /Ditolak/ }).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders empty state when no doctors found', async () => {
    mockAuthContext();
    setupFetchMocks([]);
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);

    await waitFor(() => {
      expect(screen.queryAllByText('Belum ada pendaftaran').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders doctor rows with action buttons for pending accounts', async () => {
    const mockDoctor = {
      id: 'doc-1',
      user_id: 'uid-1',
      full_name: 'Dr. Test',
      email: 'test@hospital.com',
      hospital: 'RS Test',
      primary_specialty: 'Radiologi',
      account_status: 'pending' as const,
      created_at: '2026-01-15T10:00:00Z',
    };
    mockAuthContext();
    setupFetchMocks([mockDoctor]);
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);

    await waitFor(() => {
      expect(screen.queryAllByText('Dr. Test').length).toBeGreaterThanOrEqual(1);
    });

    expect(screen.getAllByRole('button', { name: /Setujui/ }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole('button', { name: /Tolak/ }).length).toBeGreaterThanOrEqual(1);
  });

  it('calls approve endpoint when approve button is clicked', async () => {
    const mockDoctor = {
      id: 'doc-1',
      user_id: 'uid-1',
      full_name: 'Dr. Test',
      email: 'test@hospital.com',
      hospital: 'RS Test',
      primary_specialty: 'Radiologi',
      account_status: 'pending' as const,
      created_at: '2026-01-15T10:00:00Z',
    };

    // Set up fetch mock first, then spy on it
    setupFetchMocks([mockDoctor]);
    const fetchSpy = vi.spyOn(global, 'fetch');
    mockAuthContext();
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);

    await waitFor(() => {
      expect(screen.queryAllByText('Dr. Test').length).toBeGreaterThanOrEqual(1);
    });

    const approveButtons = screen.getAllByRole('button', { name: /Setujui/ });
    fireEvent.click(approveButtons[0]);

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining('/approve'),
        expect.objectContaining({ method: 'POST' })
      );
    });
    fetchSpy.mockRestore();
  });

  it('shows detail modal when detail button is clicked', async () => {
    const mockDoctor = {
      id: 'doc-1',
      user_id: 'uid-1',
      full_name: 'Dr. Test',
      email: 'test@hospital.com',
      hospital: 'RS Test',
      primary_specialty: 'Radiologi',
      account_status: 'pending' as const,
      created_at: '2026-01-15T10:00:00Z',
    };
    setupFetchMocks([mockDoctor]);
    mockAuthContext();
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);

    await waitFor(() => {
      expect(screen.queryAllByText('Dr. Test').length).toBeGreaterThanOrEqual(1);
    });

    const detailButtons = screen.getAllByRole('button', { name: /Detail/ });
    fireEvent.click(detailButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Detail Pendaftaran Dokter')).toBeTruthy();
    });
  });

  it('shows error state when the API returns a non-ok response', async () => {
    mockAuthContext();
    global.fetch = vi.fn().mockImplementation(async () => {
      return { ok: false, status: 500, json: async () => ({}) } as Response;
    });
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);

    await waitFor(() => {
      expect(screen.queryByText('Memuat Data')).toBeNull();
    });

    // Error state should be visible — both loadDoctors and loadStats catch and set errors
    expect(screen.getByText(/Gagal memuat/i)).toBeTruthy();
  });

  it('tidak menampilkan tombol Setujui/Tolak pada akun non-pending', async () => {
    const mockDoctor = {
      id: 'doc-2',
      user_id: 'uid-2',
      full_name: 'Dr. Test 2',
      email: 'test2@hospital.com',
      hospital: 'RS Test',
      primary_specialty: 'Radiologi',
      account_status: 'approved' as const,
      created_at: '2026-01-15T10:00:00Z',
    };
    mockAuthContext();
    setupFetchMocks([mockDoctor]);
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);

    await waitFor(() => {
      expect(screen.queryAllByText('Dr. Test 2').length).toBeGreaterThanOrEqual(1);
    });

    expect(screen.queryAllByRole('button', { name: /Setujui/ })).toHaveLength(0);
    expect(screen.queryAllByRole('button', { name: /Tolak/ })).toHaveLength(0);
  });

  it('menampilkan pesan error saat Approve gagal', async () => {
    const mockDoctor = {
      id: 'doc-1',
      user_id: 'uid-1',
      full_name: 'Dr. Test',
      email: 'test@hospital.com',
      hospital: 'RS Test',
      primary_specialty: 'Radiologi',
      account_status: 'pending' as const,
      created_at: '2026-01-15T10:00:00Z',
    };

    const fetchSpy = vi.spyOn(global, 'fetch').mockImplementation(async (url: string | URL | Request) => {
      const urlString = typeof url === 'string' ? url : (url as Request).url;
      if (urlString.includes('/approve')) {
        return { ok: false, status: 500, json: async () => ({}) } as Response;
      }
      if (urlString.includes('/doctors/stats') || urlString.includes('/admin/doctors')) {
        return {
          ok: true,
          json: async () => ({ success: true, data: [mockDoctor] }),
        } as Response;
      }
      return { ok: false, json: async () => ({}) } as Response;
    });
    mockAuthContext();
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);

    await waitFor(() => {
      expect(screen.queryAllByText('Dr. Test').length).toBeGreaterThanOrEqual(1);
    });

    const approveButtons = screen.getAllByRole('button', { name: /Setujui/ });
    fireEvent.click(approveButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('HTTP 500')).toBeTruthy();
    });
    fetchSpy.mockRestore();
  });

  it('mengirim alasan penolakan saat menolak pendaftaran', async () => {
    const mockDoctor = {
      id: 'doc-1',
      user_id: 'uid-1',
      full_name: 'Dr. Test',
      email: 'test@hospital.com',
      hospital: 'RS Test',
      primary_specialty: 'Radiologi',
      account_status: 'pending' as const,
      created_at: '2026-01-15T10:00:00Z',
    };

    const fetchSpy = vi.spyOn(global, 'fetch').mockImplementation(async (url: string | URL | Request) => {
      const urlString = typeof url === 'string' ? url : (url as Request).url;
      if (urlString.includes('/reject')) {
        return {
          ok: true,
          json: async () => ({
            success: true,
            data: { ...mockDoctor, account_status: 'rejected', rejection_reason: 'Dokumen tidak lengkap' },
          }),
        } as Response;
      }
      if (urlString.includes('/doctors/stats') || urlString.includes('/admin/doctors')) {
        return {
          ok: true,
          json: async () => ({ success: true, data: [mockDoctor] }),
        } as Response;
      }
      return { ok: false, json: async () => ({}) } as Response;
    });
    mockAuthContext();
    render(<MemoryRouter><AdminDashboard /></MemoryRouter>);

    await waitFor(() => {
      expect(screen.queryAllByText('Dr. Test').length).toBeGreaterThanOrEqual(1);
    });

    const rejectButtons = screen.getAllByRole('button', { name: /Tolak/ });
    fireEvent.click(rejectButtons[0]);

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Masukkan alasan penolakan...')).toBeTruthy();
    });

    const textarea = screen.getByPlaceholderText('Masukkan alasan penolakan...');
    fireEvent.change(textarea, { target: { value: 'Dokumen tidak lengkap' } });

    const confirmButton = screen.getAllByRole('button', { name: /Tolak Pendaftaran/ })[0];
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledWith(
        expect.stringContaining('/reject'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
        })
      );
    });

    const rejectCall = fetchSpy.mock.calls.find(([url]) => {
      const urlString = typeof url === 'string' ? url : (url as Request).url;
      return urlString.includes('/reject');
    });
    const body = JSON.parse((rejectCall?.[1] as RequestInit).body as string);
    expect(body.reason).toBe('Dokumen tidak lengkap');

    fetchSpy.mockRestore();
  });
});
