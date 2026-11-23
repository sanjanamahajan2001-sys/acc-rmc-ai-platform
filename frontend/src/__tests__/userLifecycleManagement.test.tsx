import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AdminUserManagementPage } from '../pages/AdminUserManagementPage';
import { adminUserService } from '../services/adminUserService';
import { AuthProvider } from '../context/AuthContext';
import { apiClient, setAuthToken, clearAuthToken } from '../services/apiClient';
import { UserIdentity } from '../types/auth';

// Mock admin user service
vi.mock('../services/adminUserService', () => ({
  adminUserService: {
    getUsers: vi.fn(),
    getUserById: vi.fn(),
    createUser: vi.fn(),
    resetPassword: vi.fn(),
    activateUser: vi.fn(),
    deactivateUser: vi.fn(),
    deleteUser: vi.fn(),
  },
}));

const mockUsersData = {
  items: [
    {
      id: 'usr-super-1',
      username: 'superadmin',
      email: 'super@acc-rmc.in',
      full_name: 'Master Admin',
      account_status: 'ACTIVE',
      password_status: 'NORMAL',
      must_change_password: false,
      last_login_at: '2026-09-16T08:00:00Z',
      created_at: '2026-09-01T00:00:00Z',
      updated_at: '2026-09-16T08:00:00Z',
      version: 1,
      roles: ['SUPER_ADMIN'],
    },
    {
      id: 'usr-target-2',
      username: 'operator1',
      email: 'operator1@acc-rmc.in',
      full_name: 'Plant Operator One',
      account_status: 'ACTIVE',
      password_status: 'NORMAL',
      must_change_password: false,
      last_login_at: '2026-09-15T12:00:00Z',
      created_at: '2026-09-02T00:00:00Z',
      updated_at: '2026-09-15T12:00:00Z',
      version: 2,
      roles: ['PLANT_OPERATOR'],
    },
    {
      id: 'usr-inactive-3',
      username: 'inactiveuser',
      email: 'inactive@acc-rmc.in',
      full_name: 'Inactive User',
      account_status: 'DEACTIVATED',
      password_status: 'NORMAL',
      must_change_password: false,
      last_login_at: null,
      created_at: '2026-09-03T00:00:00Z',
      updated_at: '2026-09-03T00:00:00Z',
      version: 1,
      roles: ['LAB_TECHNICIAN'],
    },
  ],
  total: 3,
  page: 1,
  page_size: 50,
  metrics: {
    total_users: 3,
    active_users: 2,
    administrators: 1,
    password_pending: 0,
  },
};

const mockAdminUser: UserIdentity = {
  id: 'usr-super-1',
  username: 'superadmin',
  email: 'super@acc-rmc.in',
  full_name: 'Master Admin',
  roles: ['SUPER_ADMIN'],
  account_status: 'ACTIVE',
  password_status: 'NORMAL',
  must_change_password: false,
};

describe('Phase 10: Admin User Lifecycle Management UX', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearAuthToken();
    sessionStorage.clear();
    localStorage.clear();

    // Mock clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });

    // Mock apiClient.get('/auth/me') for AuthProvider
    vi.spyOn(apiClient, 'get').mockImplementation(async (endpoint: string) => {
      if (endpoint === '/auth/me') {
        return mockAdminUser;
      }
      return {};
    });

    setAuthToken('mock-superadmin-token');
    (adminUserService.getUsers as any).mockResolvedValue(mockUsersData);
  });

  // ==========================================
  // RESET PASSWORD TESTS
  // ==========================================
  it('1. Reset Password action button appears for eligible user', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Plant Operator One')).toBeInTheDocument();
    });

    const resetButtons = screen.getAllByRole('button', { name: /reset/i });
    expect(resetButtons.length).toBeGreaterThan(0);
  });

  it('2. Clicking Reset opens confirmation dialog with policy warning', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Plant Operator One')).toBeInTheDocument();
    });

    const resetButtons = screen.getAllByRole('button', { name: /reset/i });
    fireEvent.click(resetButtons[1]); // target user operator1

    await waitFor(() => {
      expect(screen.getByText('Reset User Password')).toBeInTheDocument();
      expect(screen.getByText(/72 hours/i)).toBeInTheDocument();
    });
  });

  it('3. Certified reset-password API is called on confirm and displays one-time credential modal', async () => {
    (adminUserService.resetPassword as any).mockResolvedValueOnce({
      user_id: 'usr-target-2',
      username: 'operator1',
      temporary_password: 'NewTempPass#2026',
      expires_at: '2026-09-19T08:00:00Z',
      message: 'Password has been reset.',
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Plant Operator One')).toBeInTheDocument();
    });

    const resetButtons = screen.getAllByRole('button', { name: /reset/i });
    fireEvent.click(resetButtons[1]);

    await waitFor(() => {
      expect(screen.getByText('Reset User Password')).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole('button', { name: /confirm password reset/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(adminUserService.resetPassword).toHaveBeenCalledWith('usr-target-2');
      expect(screen.getByText('Password Reset Successfully')).toBeInTheDocument();
      expect(screen.getByText('NewTempPass#2026')).toBeInTheDocument();
    });

    // Copy action
    const copyBtn = screen.getByRole('button', { name: /copy password/i });
    fireEvent.click(copyBtn);
    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('NewTempPass#2026');
      expect(screen.getByText('Copied!')).toBeInTheDocument();
    });

    // Done button closes modal and purges credential
    const doneBtn = screen.getByRole('button', { name: /done & return to directory/i });
    fireEvent.click(doneBtn);

    await waitFor(() => {
      expect(screen.queryByText('NewTempPass#2026')).not.toBeInTheDocument();
      expect(sessionStorage.getItem('temporary_password')).toBeNull();
      expect(localStorage.getItem('temporary_password')).toBeNull();
    });
  });

  it('4. Reset API 403 / 409 errors are displayed cleanly in dialog', async () => {
    (adminUserService.resetPassword as any).mockRejectedValueOnce({
      data: {
        detail: 'Plant Administrators cannot reset passwords for a Master Administrator account.',
      },
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Plant Operator One')).toBeInTheDocument();
    });

    const resetButtons = screen.getAllByRole('button', { name: /reset/i });
    fireEvent.click(resetButtons[1]);

    const confirmBtn = screen.getByRole('button', { name: /confirm password reset/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByText(/Plant Administrators cannot reset passwords/i)).toBeInTheDocument();
    });
  });

  // ==========================================
  // ACTIVATE TESTS
  // ==========================================
  it('5. Activate confirmation opens and calls certified activate API', async () => {
    (adminUserService.activateUser as any).mockResolvedValueOnce({
      id: 'usr-inactive-3',
      username: 'inactiveuser',
      account_status: 'ACTIVE',
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Inactive User')).toBeInTheDocument();
    });

    const inactiveRow = screen.getByText('(@inactiveuser)').closest('tr')!;
    const activateBtn = within(inactiveRow).getByRole('button', { name: /activate/i });
    fireEvent.click(activateBtn);

    await waitFor(() => {
      expect(screen.getByText('Activate User Account')).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole('button', { name: /activate account/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(adminUserService.activateUser).toHaveBeenCalledWith('usr-inactive-3');
      expect(screen.getByText(/successfully activated/i)).toBeInTheDocument();
    });
  });

  // ==========================================
  // DEACTIVATE TESTS
  // ==========================================
  it('6. Deactivate confirmation opens and calls certified deactivate API', async () => {
    (adminUserService.deactivateUser as any).mockResolvedValueOnce({
      id: 'usr-target-2',
      username: 'operator1',
      account_status: 'DEACTIVATED',
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Plant Operator One')).toBeInTheDocument();
    });

    const deactivateButtons = screen.getAllByRole('button', { name: /deactivate/i });
    fireEvent.click(deactivateButtons[1]); // target user operator1

    await waitFor(() => {
      expect(screen.getByText('Deactivate User Account')).toBeInTheDocument();
    });

    const confirmBtn = screen.getByRole('button', { name: /deactivate account/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(adminUserService.deactivateUser).toHaveBeenCalledWith('usr-target-2');
      expect(screen.getByText(/successfully deactivated/i)).toBeInTheDocument();
    });
  });

  it('7. Self-deactivation and Last SUPER_ADMIN errors are handled gracefully', async () => {
    (adminUserService.deactivateUser as any).mockRejectedValueOnce({
      data: {
        detail: 'Cannot deactivate the last remaining active Master Administrator.',
      },
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('(@superadmin)')).toBeInTheDocument();
    });

    const deactivateButtons = screen.getAllByRole('button', { name: /deactivate/i });
    fireEvent.click(deactivateButtons[0]);

    const confirmBtn = screen.getByRole('button', { name: /deactivate account/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(screen.getByText(/Cannot deactivate the last remaining active Master Administrator/i)).toBeInTheDocument();
    });
  });

  // ==========================================
  // DELETE TESTS
  // ==========================================
  it('8. Delete confirmation opens and enforces type-to-confirm safeguard', async () => {
    (adminUserService.deleteUser as any).mockResolvedValueOnce({
      message: "User 'operator1' successfully deleted.",
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Plant Operator One')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
    fireEvent.click(deleteButtons[1]); // target user operator1

    await waitFor(() => {
      expect(screen.getByText('Permanently Delete User Account')).toBeInTheDocument();
    });

    const deleteConfirmBtn = screen.getByRole('button', { name: /permanently delete user/i });
    expect(deleteConfirmBtn).toBeDisabled();

    // Type incorrect text
    const input = screen.getByPlaceholderText('operator1');
    fireEvent.change(input, { target: { value: 'wrongname' } });
    expect(deleteConfirmBtn).toBeDisabled();

    // Type exact username
    fireEvent.change(input, { target: { value: 'operator1' } });
    expect(deleteConfirmBtn).not.toBeDisabled();

    fireEvent.click(deleteConfirmBtn);

    await waitFor(() => {
      expect(adminUserService.deleteUser).toHaveBeenCalledWith('usr-target-2');
      expect(screen.getByText(/successfully deleted/i)).toBeInTheDocument();
    });
  });

  it('9. User detail modal offers lifecycle actions', async () => {
    (adminUserService.getUserById as any).mockResolvedValueOnce({
      id: 'usr-target-2',
      username: 'operator1',
      email: 'operator1@acc-rmc.in',
      full_name: 'Plant Operator One',
      account_status: 'ACTIVE',
      password_status: 'NORMAL',
      must_change_password: false,
      last_login_at: null,
      created_at: '2026-09-02T00:00:00Z',
      updated_at: '2026-09-15T12:00:00Z',
      version: 2,
      roles: ['PLANT_OPERATOR'],
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Plant Operator One')).toBeInTheDocument();
    });

    const inspectButtons = screen.getAllByRole('button', { name: /inspect/i });
    fireEvent.click(inspectButtons[1]);

    await waitFor(() => {
      expect(screen.getByText('User Account Overview')).toBeInTheDocument();
      expect(screen.getByText('Authentication State')).toBeInTheDocument();
    });
  });
});
