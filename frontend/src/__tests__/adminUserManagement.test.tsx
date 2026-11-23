import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AdminUserManagementPage } from '../pages/AdminUserManagementPage';
import { adminUserService } from '../services/adminUserService';
import { AuthProvider } from '../context/AuthContext';
import { ProtectedRoute } from '../components/common/ProtectedRoute';
import { AccessDenied } from '../components/common/AccessDenied';
import { apiClient, setAuthToken, clearAuthToken } from '../services/apiClient';
import { UserIdentity, CanonicalRole } from '../types/auth';

// Mock admin user service
vi.mock('../services/adminUserService', () => ({
  adminUserService: {
    getUsers: vi.fn(),
    getUserById: vi.fn(),
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
    {
      id: 'usr-3333-4444',
      username: 'jdoe',
      email: 'jdoe@acc-rmc.in',
      full_name: 'John Doe',
      account_status: 'ACTIVE' as const,
      password_status: 'TEMPORARY' as const,
      must_change_password: true,
      last_login_at: null,
      created_at: '2026-09-15T10:00:00Z',
      updated_at: '2026-09-15T10:00:00Z',
      version: 1,
      roles: ['QUALITY_MANAGER'],
    },
  ],
  total: 2,
  page: 1,
  page_size: 50,
  metrics: {
    total_users: 2,
    active_users: 2,
    administrators: 1,
    password_pending: 1,
  },
};

const mockUserDetail = {
  id: 'usr-1111-2222',
  username: 'admin',
  email: 'admin@acc-rmc.in',
  full_name: 'System Administrator',
  account_status: 'ACTIVE' as const,
  password_status: 'ACTIVE' as const,
  must_change_password: false,
  failed_login_attempts: 0,
  last_login_at: '2026-09-16T08:00:00Z',
  last_password_change_at: '2026-09-10T00:00:00Z',
  created_at: '2026-09-01T00:00:00Z',
  updated_at: '2026-09-16T08:00:00Z',
  version: 1,
  roles: ['SUPER_ADMIN', 'ADMIN'],
};

describe('Phase 8: Admin User Management Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearAuthToken();
  });

  it('1. Unauthenticated user accessing admin dashboard is redirected to login', async () => {
    vi.spyOn(apiClient, 'get').mockRejectedValue(new Error('No token'));

    render(
      <MemoryRouter initialEntries={['/acc/admin/users']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/acc/admin/users"
              element={
                <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'ADMIN']}>
                  <AdminUserManagementPage />
                </ProtectedRoute>
              }
            />
            <Route path="/acc/login" element={<div>LoginPage Mock</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('LoginPage Mock')).toBeInTheDocument();
    });
  });

  const nonAdminRoles: { role: CanonicalRole; name: string }[] = [
    { role: 'PLANT_OPERATOR', name: 'Plant Operator' },
    { role: 'LAB_TECHNICIAN', name: 'Lab Tech' },
    { role: 'ANALYST_VIEWER', name: 'Analyst Viewer' },
    { role: 'QUALITY_HEAD', name: 'Quality Head' },
  ];

  nonAdminRoles.forEach(({ role, name }) => {
    it(`2. Non-admin role (${role}) receives AccessDenied (403)`, async () => {
      const mockUser: UserIdentity = {
        id: `usr-${role.toLowerCase()}`,
        username: role.toLowerCase(),
        email: `${role.toLowerCase()}@acc-rmc.in`,
        full_name: name,
        roles: [role],
        must_change_password: false,
        account_status: 'ACTIVE',
        password_status: 'NORMAL',
      };

      setAuthToken(`valid-${role.toLowerCase()}-token`);
      vi.spyOn(apiClient, 'get').mockResolvedValue(mockUser);

      render(
        <MemoryRouter initialEntries={['/acc/admin/users']}>
          <AuthProvider>
            <Routes>
              <Route
                path="/acc/admin/users"
                element={
                  <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'ADMIN']}>
                    <AdminUserManagementPage />
                  </ProtectedRoute>
                }
              />
              <Route path="/access-denied" element={<AccessDenied />} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('Access Restricted (403 Forbidden)')).toBeInTheDocument();
      });
    });
  });

  it('3. SUPER_ADMIN user can access admin dashboard directly', async () => {
    const mockSuperAdmin: UserIdentity = {
      id: 'usr-super-1',
      username: 'superadmin',
      email: 'superadmin@acc-rmc.in',
      full_name: 'Super Administrator',
      roles: ['SUPER_ADMIN'],
      must_change_password: false,
      account_status: 'ACTIVE',
      password_status: 'NORMAL',
    };

    setAuthToken('valid-super-token');
    vi.spyOn(apiClient, 'get').mockResolvedValue(mockSuperAdmin);
    (adminUserService.getUsers as any).mockResolvedValueOnce(mockUsersData);

    render(
      <MemoryRouter initialEntries={['/acc/admin/users']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/acc/admin/users"
              element={
                <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'ADMIN']}>
                  <AdminUserManagementPage />
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('User Management Dashboard')).toBeInTheDocument();
    });
  });

  it('4. ADMIN user renders dashboard with summary metrics cards', async () => {
    const mockAdmin: UserIdentity = {
      id: 'usr-admin-1',
      username: 'admin',
      email: 'admin@acc-rmc.in',
      full_name: 'Admin User',
      roles: ['ADMIN'],
      must_change_password: false,
      account_status: 'ACTIVE',
      password_status: 'NORMAL',
    };

    setAuthToken('valid-admin-token');
    vi.spyOn(apiClient, 'get').mockResolvedValue(mockAdmin);
    (adminUserService.getUsers as any).mockResolvedValueOnce(mockUsersData);

    render(
      <MemoryRouter initialEntries={['/acc/admin/users']}>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('User Management Dashboard')).toBeInTheDocument();
    });

    // Verify metrics rendered
    await waitFor(() => {
      expect(screen.getByText('Total Registered')).toBeInTheDocument();
      expect(screen.getByText('Active Accounts')).toBeInTheDocument();
      expect(screen.getByText('Administrators')).toBeInTheDocument();
      expect(screen.getByText('Password Pending')).toBeInTheDocument();
    });
  });

  it('5. Directory renders user records from API contract correctly', async () => {
    (adminUserService.getUsers as any).mockResolvedValueOnce(mockUsersData);

    render(
      <MemoryRouter initialEntries={['/acc/admin/users']}>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('System Administrator')).toBeInTheDocument();
      expect(screen.getByText('(@admin)')).toBeInTheDocument();
      expect(screen.getByText('admin@acc-rmc.in')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('(@jdoe)')).toBeInTheDocument();
    });
  });

  it('6. Search input calls API with query parameter', async () => {
    (adminUserService.getUsers as any).mockResolvedValue(mockUsersData);

    render(
      <MemoryRouter initialEntries={['/acc/admin/users']}>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    const searchInput = screen.getByPlaceholderText('Search by username, full name, or email...');
    fireEvent.change(searchInput, { target: { value: 'jdoe' } });

    await waitFor(() => {
      expect(adminUserService.getUsers).toHaveBeenCalledWith(
        expect.objectContaining({
          q: 'jdoe',
        })
      );
    });
  });

  it('7. Clicking Inspect opens UserDetailModal and fetches user details', async () => {
    (adminUserService.getUsers as any).mockResolvedValueOnce(mockUsersData);
    (adminUserService.getUserById as any).mockResolvedValueOnce(mockUserDetail);

    render(
      <MemoryRouter initialEntries={['/acc/admin/users']}>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('System Administrator')).toBeInTheDocument();
    });

    const inspectButtons = screen.getAllByRole('button', { name: /inspect/i });
    fireEvent.click(inspectButtons[0]);

    await waitFor(() => {
      expect(adminUserService.getUserById).toHaveBeenCalledWith('usr-1111-2222');
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('User Account Overview')).toBeInTheDocument();
      expect(screen.getByText('Assigned RBAC Roles')).toBeInTheDocument();
    });
  });

  it('8. Inspect modal does NOT expose passwords, hashes, or secret keys', async () => {
    (adminUserService.getUsers as any).mockResolvedValueOnce(mockUsersData);
    (adminUserService.getUserById as any).mockResolvedValueOnce(mockUserDetail);

    render(
      <MemoryRouter initialEntries={['/acc/admin/users']}>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('System Administrator')).toBeInTheDocument();
    });

    const inspectButtons = screen.getAllByRole('button', { name: /inspect/i });
    fireEvent.click(inspectButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    // Ensure zero password hashes or secrets in DOM
    const bodyText = document.body.textContent || '';
    expect(bodyText).not.toContain('password_hash');
    expect(bodyText).not.toContain('$2b$12$');
    expect(bodyText).not.toContain('argon2');
    expect(bodyText).not.toContain('token');
  });

  it('9. Empty state handles zero accounts gracefully', async () => {
    (adminUserService.getUsers as any).mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
      metrics: {
        total_users: 0,
        active_users: 0,
        administrators: 0,
        password_pending: 0,
      },
    });

    render(
      <MemoryRouter initialEntries={['/acc/admin/users']}>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No accounts found')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your search criteria or filter selections.')).toBeInTheDocument();
    });
  });
});
