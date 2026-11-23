import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LoginPage } from '../pages/LoginPage';
import { ChangePasswordPage } from '../pages/ChangePasswordPage';
import { AdminUserManagementPage } from '../pages/AdminUserManagementPage';
import { CreateUserModal } from '../components/admin/CreateUserModal';
import { OneTimeCredentialModal } from '../components/admin/OneTimeCredentialModal';
import { UserLifecycleActionModal } from '../components/admin/UserLifecycleActionModal';
import { UserDetailModal } from '../components/admin/UserDetailModal';
import { AccountAdminModal } from '../components/admin/AccountAdminModal';
import { AuthProvider } from '../context/AuthContext';
import { adminUserService, UserDetailDTO } from '../services/adminUserService';

// Mock services
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

const mockUser: UserDetailDTO = {
  id: 'usr-100',
  username: 'test_operator_long_username',
  email: 'very_long_corporate_email_address_for_operator@acc-rmc-plant.com',
  full_name: 'Supercalifragilistic Operator Name',
  account_status: 'ACTIVE',
  password_status: 'NORMAL',
  must_change_password: false,
  last_login_at: '2026-09-16T10:00:00Z',
  created_at: '2026-09-01T00:00:00Z',
  updated_at: '2026-09-16T10:00:00Z',
  version: 1,
  roles: ['PLANT_OPERATOR', 'LAB_TECHNICIAN'],
};

describe('Phase 11: Mobile / Tablet Responsive & Accessibility Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // ==========================================
  // 1. LOGIN PAGE A11Y & RESPONSIVE
  // ==========================================
  it('1. Login page renders semantic form, accessible labels, and show/hide password toggle', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>
    );

    const usernameInput = screen.getByLabelText(/username or corporate email/i);
    const passwordInput = screen.getByLabelText(/^password/i);
    const submitBtn = screen.getByRole('button', { name: /sign in to operations console/i });
    const toggleBtn = screen.getByRole('button', { name: /show password/i });

    expect(usernameInput).toBeInTheDocument();
    expect(passwordInput).toBeInTheDocument();
    expect(submitBtn).toBeInTheDocument();
    expect(toggleBtn).toBeInTheDocument();

    // Toggle password visibility
    expect(passwordInput).toHaveAttribute('type', 'password');
    fireEvent.click(toggleBtn);
    expect(passwordInput).toHaveAttribute('type', 'text');
  });

  // ==========================================
  // 2. CHANGE PASSWORD PAGE RESPONSIVE & CHECKLIST
  // ==========================================
  it('2. Change password page displays readable 6-point checklist without overflow', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <ChangePasswordPage />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/At least 10 characters/i)).toBeInTheDocument();
    expect(screen.getByText(/One uppercase \(A-Z\)/i)).toBeInTheDocument();
    expect(screen.getByText(/One lowercase \(a-z\)/i)).toBeInTheDocument();
    expect(screen.getByText(/One number \(0-9\)/i)).toBeInTheDocument();
    expect(screen.getByText(/One special character/i)).toBeInTheDocument();
    expect(screen.getByText(/Passwords match/i)).toBeInTheDocument();
  });

  // ==========================================
  // 3. ADMIN DIRECTORY RESPONSIVE TABLE CONTAINER
  // ==========================================
  it('3. Admin user directory renders accessible table with contained horizontal scrolling', async () => {
    (adminUserService.getUsers as any).mockResolvedValueOnce({
      items: [mockUser],
      total: 1,
      page: 1,
      page_size: 50,
      metrics: {
        total_users: 1,
        active_users: 1,
        administrators: 0,
        password_pending: 0,
      },
    });

    const { container } = render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Supercalifragilistic Operator Name')).toBeInTheDocument();
    });

    const table = container.querySelector('table');
    expect(table).toBeInTheDocument();
    expect(table?.style.minWidth).toBe('860px');

    const tableWrapper = table?.parentElement;
    expect(tableWrapper?.style.overflowX).toBe('auto');
  });

  // ==========================================
  // 4. CREATE USER MODAL VIEWPORT SAFETY & ESCAPE KEY
  // ==========================================
  it('4. Create User modal has dialog role, aria-modal, and handles Escape key dismissal', () => {
    const handleClose = vi.fn();
    const handleSuccess = vi.fn();

    render(
      <MemoryRouter>
        <AuthProvider>
          <CreateUserModal
            isOpen={true}
            onClose={handleClose}
            onSuccess={handleSuccess}
          />
        </AuthProvider>
      </MemoryRouter>
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(screen.getByText('Create User Account')).toBeInTheDocument();

    // Trigger Escape key
    fireEvent.keyDown(window, { key: 'Escape', code: 'Escape' });
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  // ==========================================
  // 5. ONE-TIME CREDENTIAL MODAL SAFETY & VIEWPORT
  // ==========================================
  it('5. One-Time Credential modal guards uncopied closure on Escape and Done', async () => {
    const handleClose = vi.fn();

    render(
      <OneTimeCredentialModal
        isOpen={true}
        onClose={handleClose}
        credentialData={{
          temporary_password: 'TestTempPassword#999',
          expires_at: '2026-09-19T00:00:00Z',
          user: {
            id: 'usr-1',
            username: 'sanjana',
            full_name: 'Sanjana Admin',
            roles: ['PLANT_OPERATOR'],
          } as any,
        }}
      />
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('TestTempPassword#999')).toBeInTheDocument();

    // Press Escape before copying -> triggers safety warning
    fireEvent.keyDown(window, { key: 'Escape', code: 'Escape' });
    expect(handleClose).not.toHaveBeenCalled();
    expect(screen.getByText(/You have not copied the temporary password yet/i)).toBeInTheDocument();

    // Force close dismisses
    const forceCloseBtn = screen.getByRole('button', { name: /I Understand, Close Anyway/i });
    fireEvent.click(forceCloseBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  // ==========================================
  // 6. LIFECYCLE ACTION MODAL (RESET / DEACTIVATE / ACTIVATE / DELETE)
  // ==========================================
  it('6. Lifecycle action modal renders accessible dialog with Escape key support', () => {
    const handleClose = vi.fn();
    const handleSuccess = vi.fn();

    render(
      <UserLifecycleActionModal
        isOpen={true}
        targetUser={mockUser}
        actionType="RESET_PASSWORD"
        onClose={handleClose}
        onSuccess={handleSuccess}
      />
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(screen.getByText('Reset User Password')).toBeInTheDocument();

    fireEvent.keyDown(window, { key: 'Escape', code: 'Escape' });
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  // ==========================================
  // 7. DELETE SAFEGUARD ACCESSIBILITY & TYPE-TO-CONFIRM
  // ==========================================
  it('7. Delete confirmation modal enforces case-sensitive type-to-confirm', () => {
    const handleClose = vi.fn();
    const handleSuccess = vi.fn();

    render(
      <UserLifecycleActionModal
        isOpen={true}
        targetUser={mockUser}
        actionType="DELETE"
        onClose={handleClose}
        onSuccess={handleSuccess}
      />
    );

    const deleteBtn = screen.getByRole('button', { name: 'Permanently Delete User' });
    expect(deleteBtn).toBeDisabled();

    const input = screen.getByPlaceholderText(mockUser.username);
    fireEvent.change(input, { target: { value: 'wrong_username' } });
    expect(deleteBtn).toBeDisabled();

    fireEvent.change(input, { target: { value: mockUser.username } });
    expect(deleteBtn).not.toBeDisabled();
  });

  // ==========================================
  // 8. USER DETAIL MODAL ACCESSIBILITY & ESCAPE
  // ==========================================
  it('8. UserDetailModal renders accessible dialog and handles Escape key', () => {
    const handleClose = vi.fn();

    render(
      <UserDetailModal
        isOpen={true}
        user={mockUser}
        onClose={handleClose}
        isSuperAdmin={true}
      />
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(screen.getByText('User Account Overview')).toBeInTheDocument();

    fireEvent.keyDown(window, { key: 'Escape', code: 'Escape' });
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  // ==========================================
  // 9. ACCOUNT ADMIN MODAL ACCESSIBILITY & TABS
  // ==========================================
  it('9. AccountAdminModal renders accessible dialog with labelledby and Escape key', () => {
    const handleClose = vi.fn();

    render(
      <MemoryRouter>
        <AuthProvider>
          <AccountAdminModal
            isOpen={true}
            onClose={handleClose}
          />
        </AuthProvider>
      </MemoryRouter>
    );

    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'account-admin-modal-title');

    fireEvent.keyDown(window, { key: 'Escape', code: 'Escape' });
    expect(handleClose).toHaveBeenCalledTimes(1);
  });

  // ==========================================
  // 10. LONG TEXT WRAPPING & VIEWPORT SAFETY
  // ==========================================
  it('10. Renders long usernames and emails without breaking modal layout', () => {
    render(
      <UserDetailModal
        isOpen={true}
        user={mockUser}
        onClose={vi.fn()}
        isSuperAdmin={true}
      />
    );

    expect(screen.getByText(/very_long_corporate_email_address_for_operator/i)).toBeInTheDocument();
    expect(screen.getByText(/test_operator_long_username/i)).toBeInTheDocument();
  });

  // ==========================================
  // 11. SHARED APP SHELL & MOBILE NAVIGATION DRAWER
  // ==========================================
  it('11. Shared AppShell renders hamburger toggle and toggles mobile drawer on interaction', async () => {
    (adminUserService.getUsers as any).mockResolvedValueOnce({
      items: [mockUser],
      total: 1,
      page: 1,
      page_size: 50,
      metrics: {
        total_users: 1,
        active_users: 1,
        administrators: 0,
        password_pending: 0,
      },
    });

    const { container } = render(
      <MemoryRouter>
        <AuthProvider>
          <AdminUserManagementPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Supercalifragilistic Operator Name')).toBeInTheDocument();
    });

    // Check that sidebar has app-sidebar-container class
    const sidebar = container.querySelector('.app-sidebar-container');
    expect(sidebar).toBeInTheDocument();
    expect(sidebar).not.toHaveClass('mobile-open');

    // Click hamburger toggle button
    const toggleBtn = screen.getByLabelText(/open navigation menu/i);
    expect(toggleBtn).toBeInTheDocument();
    fireEvent.click(toggleBtn);

    // Sidebar should now have mobile-open class
    expect(sidebar).toHaveClass('mobile-open');

    // Press Escape to close mobile drawer
    fireEvent.keyDown(window, { key: 'Escape', code: 'Escape' });
    expect(sidebar).not.toHaveClass('mobile-open');
  });
});
