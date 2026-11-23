import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
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
  },
}));

const mockUsersData = {
  items: [
    {
      id: 'usr-1111-2222',
      username: 'admin',
      email: 'admin@acc-rmc.in',
      full_name: 'System Administrator',
      account_status: 'ACTIVE' as const,
      password_status: 'ACTIVE' as const,
      must_change_password: false,
      last_login_at: '2026-09-16T08:00:00Z',
      created_at: '2026-09-01T00:00:00Z',
      updated_at: '2026-09-16T08:00:00Z',
      version: 1,
      roles: ['SUPER_ADMIN', 'ADMIN'],
    },
  ],
  total: 1,
  page: 1,
  page_size: 50,
  metrics: {
    total_users: 1,
    active_users: 1,
    administrators: 1,
    password_pending: 0,
  },
};

const mockCreateResponse = {
  user: {
    id: 'usr-new-9999',
    username: 'rsharma',
    email: 'rsharma@acc-rmc.in',
    full_name: 'Ramesh Sharma',
    account_status: 'ACTIVE',
    password_status: 'CHANGE_REQUIRED',
    must_change_password: true,
    last_login_at: null,
    created_at: '2026-09-16T10:00:00Z',
    updated_at: '2026-09-16T10:00:00Z',
    version: 1,
    roles: ['PLANT_OPERATOR'],
  },
  temporary_password: 'TempPassword#2026',
  expires_at: '2026-09-17T10:00:00Z',
  message: 'User created successfully. Transfer temporary password securely to the user.',
};

describe('Phase 9: Create User & One-Time Credential UX', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearAuthToken();
    (adminUserService.getUsers as any).mockResolvedValue(mockUsersData);

    // Mock clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockResolvedValue(undefined),
      },
    });
  });

  const setupAdminSession = (isSuperAdmin = false) => {
    const mockAdmin: UserIdentity = {
      id: isSuperAdmin ? 'usr-super-1' : 'usr-admin-1',
      username: isSuperAdmin ? 'superadmin' : 'admin',
      email: isSuperAdmin ? 'super@acc-rmc.in' : 'admin@acc-rmc.in',
      full_name: isSuperAdmin ? 'Super Admin' : 'Admin User',
      roles: isSuperAdmin ? ['SUPER_ADMIN'] : ['ADMIN'],
      must_change_password: false,
      account_status: 'ACTIVE',
      password_status: 'NORMAL',
    };
    setAuthToken('valid-admin-token');
    vi.spyOn(apiClient, 'get').mockResolvedValue(mockAdmin);
  };

  it('1. Create User button opens creation modal form', async () => {
    setupAdminSession(false);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('User Management Dashboard')).toBeInTheDocument();
    });

    const createButton = screen.getByRole('button', { name: /create user/i });
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('Create User Account')).toBeInTheDocument();
    });
  });

  it('2. Required form validation prevents submission with empty fields', async () => {
    setupAdminSession(false);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    const createButton = screen.getByRole('button', { name: /create user/i });
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(screen.getByText('Create User Account')).toBeInTheDocument();
    });

    const submitBtn = screen.getByRole('button', { name: /create account/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('Full name is required.')).toBeInTheDocument();
      expect(screen.getByText('Username is required.')).toBeInTheDocument();
      expect(screen.getByText('Corporate email address is required.')).toBeInTheDocument();
    });

    expect(adminUserService.createUser).not.toHaveBeenCalled();
  });

  it('3. ADMIN cannot view/assign SUPER_ADMIN role option', async () => {
    setupAdminSession(false); // standard ADMIN

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    const createButton = screen.getByRole('button', { name: /create user/i });
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(screen.getByText('Create User Account')).toBeInTheDocument();
    });

    // In assignable role buttons, SUPER_ADMIN should not exist
    const roleButtons = screen.getAllByRole('button');
    const roleTexts = roleButtons.map((b) => b.textContent);
    expect(roleTexts.some((t) => t?.includes('SUPER_ADMIN'))).toBe(false);
  });

  it('4. SUPER_ADMIN can view/assign SUPER_ADMIN role option', async () => {
    setupAdminSession(true); // SUPER_ADMIN

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    const createButton = screen.getByRole('button', { name: /create user/i });
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(screen.getByText('Create User Account')).toBeInTheDocument();
    });

    // SUPER_ADMIN button exists
    expect(screen.getByRole('button', { name: /super_admin/i })).toBeInTheDocument();
  });

  it('5. Valid submission calls API with exact certified payload and displays one-time credential modal', async () => {
    setupAdminSession(false);
    (adminUserService.createUser as any).mockResolvedValueOnce(mockCreateResponse);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    const createButton = screen.getByRole('button', { name: /create user/i });
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(screen.getByText('Create User Account')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText('e.g. Ramesh Sharma'), {
      target: { value: 'Ramesh Sharma' },
    });
    fireEvent.change(screen.getByPlaceholderText('e.g. rsharma'), {
      target: { value: 'rsharma' },
    });
    fireEvent.change(screen.getByPlaceholderText('e.g. rsharma@acc-rmc.in'), {
      target: { value: 'rsharma@acc-rmc.in' },
    });

    const submitBtn = screen.getByRole('button', { name: /create account/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(adminUserService.createUser).toHaveBeenCalledWith({
        full_name: 'Ramesh Sharma',
        username: 'rsharma',
        email: 'rsharma@acc-rmc.in',
        roles: ['PLANT_OPERATOR'],
      });
      // Credential modal should now be visible
      expect(screen.getByText('Account Provisioned Successfully')).toBeInTheDocument();
      expect(screen.getByText('TempPassword#2026')).toBeInTheDocument();
      expect(screen.getByText('One-Time Disclosure Security Notice')).toBeInTheDocument();
    });
  });

  it('6. Copy Password button writes to clipboard and shows feedback', async () => {
    setupAdminSession(false);
    (adminUserService.createUser as any).mockResolvedValueOnce(mockCreateResponse);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: /create user/i }));
    await waitFor(() => screen.getByText('Create User Account'));

    fireEvent.change(screen.getByPlaceholderText('e.g. Ramesh Sharma'), { target: { value: 'Ramesh Sharma' } });
    fireEvent.change(screen.getByPlaceholderText('e.g. rsharma'), { target: { value: 'rsharma' } });
    fireEvent.change(screen.getByPlaceholderText('e.g. rsharma@acc-rmc.in'), { target: { value: 'rsharma@acc-rmc.in' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText('TempPassword#2026')).toBeInTheDocument();
    });

    const copyBtn = screen.getByRole('button', { name: /copy password/i });
    fireEvent.click(copyBtn);

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('TempPassword#2026');
      expect(screen.getByText('Copied!')).toBeInTheDocument();
    });
  });

  it('7. Attempting to close modal before copying triggers safety warning', async () => {
    setupAdminSession(false);
    (adminUserService.createUser as any).mockResolvedValueOnce(mockCreateResponse);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: /create user/i }));
    await waitFor(() => screen.getByText('Create User Account'));

    fireEvent.change(screen.getByPlaceholderText('e.g. Ramesh Sharma'), { target: { value: 'Ramesh Sharma' } });
    fireEvent.change(screen.getByPlaceholderText('e.g. rsharma'), { target: { value: 'rsharma' } });
    fireEvent.change(screen.getByPlaceholderText('e.g. rsharma@acc-rmc.in'), { target: { value: 'rsharma@acc-rmc.in' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText('TempPassword#2026')).toBeInTheDocument();
    });

    // Close before copying
    const doneBtn = screen.getByRole('button', { name: /done & return to directory/i });
    fireEvent.click(doneBtn);

    // Warning confirmation appears
    await waitFor(() => {
      expect(screen.getByText('Credential Not Copied')).toBeInTheDocument();
      expect(screen.getByText(/You have not copied the temporary password yet/i)).toBeInTheDocument();
    });
  });

  it('8. Closing credential modal destroys ephemeral password from DOM and state', async () => {
    setupAdminSession(false);
    (adminUserService.createUser as any).mockResolvedValueOnce(mockCreateResponse);

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: /create user/i }));
    await waitFor(() => screen.getByText('Create User Account'));

    fireEvent.change(screen.getByPlaceholderText('e.g. Ramesh Sharma'), { target: { value: 'Ramesh Sharma' } });
    fireEvent.change(screen.getByPlaceholderText('e.g. rsharma'), { target: { value: 'rsharma' } });
    fireEvent.change(screen.getByPlaceholderText('e.g. rsharma@acc-rmc.in'), { target: { value: 'rsharma@acc-rmc.in' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText('TempPassword#2026')).toBeInTheDocument();
    });

    // Copy password
    fireEvent.click(screen.getByRole('button', { name: /copy password/i }));
    await waitFor(() => screen.getByText('Copied!'));

    // Close modal
    fireEvent.click(screen.getByRole('button', { name: /done & return to directory/i }));

    await waitFor(() => {
      expect(screen.queryByText('Account Provisioned Successfully')).not.toBeInTheDocument();
      expect(screen.queryByText('TempPassword#2026')).not.toBeInTheDocument();
    });

    // Password must not exist in DOM
    const bodyText = document.body.textContent || '';
    expect(bodyText).not.toContain('TempPassword#2026');
  });

  it('9. Backend duplicate conflict (409) is displayed cleanly to user', async () => {
    setupAdminSession(false);
    (adminUserService.createUser as any).mockRejectedValueOnce({
      response: {
        status: 409,
        data: {
          detail: 'A user with this username or email address already exists.',
        },
      },
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: /create user/i }));
    await waitFor(() => screen.getByText('Create User Account'));

    fireEvent.change(screen.getByPlaceholderText('e.g. Ramesh Sharma'), { target: { value: 'Ramesh Sharma' } });
    fireEvent.change(screen.getByPlaceholderText('e.g. rsharma'), { target: { value: 'rsharma' } });
    fireEvent.change(screen.getByPlaceholderText('e.g. rsharma@acc-rmc.in'), { target: { value: 'rsharma@acc-rmc.in' } });
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText('A user with this username or email address already exists.')).toBeInTheDocument();
    });
  });
});
