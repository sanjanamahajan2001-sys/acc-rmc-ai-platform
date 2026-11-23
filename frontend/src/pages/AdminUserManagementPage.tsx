import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  adminUserService,
  UserSummaryItem,
  UserDetailDTO,
  AdminUserMetrics,
  UserAdminCreateResponseDTO,
  PasswordResetResponseDTO,
} from '../services/adminUserService';
import {
  enterpriseLightTokens as tokens,
  primaryButtonBase,
  secondaryButtonBase,
  formInputStyle,
} from '../components/manual-entry/enterpriseLightTokens';
import {
  Users,
  UserCheck,
  Shield,
  KeyRound,
  Search,
  Plus,
  RefreshCw,
  Eye,
  AlertTriangle,
  UserX,
  CheckCircle2,
  Trash2,
  Check,
} from 'lucide-react';
import { AppShell } from '../components/AppShell';
import { UserDetailModal } from '../components/admin/UserDetailModal';
import { CreateUserModal } from '../components/admin/CreateUserModal';
import { OneTimeCredentialModal, OneTimeCredentialData } from '../components/admin/OneTimeCredentialModal';
import { UserLifecycleActionModal, LifecycleActionType } from '../components/admin/UserLifecycleActionModal';

export const AdminUserManagementPage: React.FC = () => {
  const { isSuperAdmin } = useAuth();

  // Directory & Metrics State
  const [users, setUsers] = useState<UserSummaryItem[]>([]);
  const [metrics, setMetrics] = useState<AdminUserMetrics>({
    total_users: 0,
    active_users: 0,
    administrators: 0,
    password_pending: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  // Modals State
  const [selectedUser, setSelectedUser] = useState<UserDetailDTO | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isLoadingModal, setIsLoadingModal] = useState(false);

  // Phase 9 Modals State
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [credentialData, setCredentialData] = useState<OneTimeCredentialData | UserAdminCreateResponseDTO | null>(null);
  const [isCredentialModalOpen, setIsCredentialModalOpen] = useState(false);

  // Phase 10 Lifecycle Modal State
  const [lifecycleAction, setLifecycleAction] = useState<LifecycleActionType | null>(null);
  const [lifecycleTargetUser, setLifecycleTargetUser] = useState<UserSummaryItem | UserDetailDTO | null>(null);
  const [isLifecycleModalOpen, setIsLifecycleModalOpen] = useState(false);

  // Load User Directory & Metrics
  const loadUsers = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await adminUserService.getUsers({
        q: searchQuery.trim() || undefined,
        account_status: statusFilter || undefined,
        role_id: roleFilter || undefined,
      });
      setUsers(response.items || []);
      if (response.metrics) {
        setMetrics(response.metrics);
      }
    } catch (err: any) {
      const msg = err?.data?.detail || err?.message || 'Unable to load administrative user directory.';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, statusFilter, roleFilter]);

  // Initial Load & Filter trigger
  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  // Handle Inspect User
  const handleInspectUser = async (userId: string) => {
    setIsLoadingModal(true);
    setIsModalOpen(true);
    try {
      const detail = await adminUserService.getUserById(userId);
      setSelectedUser(detail);
    } catch (err: any) {
      setError('Failed to fetch user details.');
      setIsModalOpen(false);
    } finally {
      setIsLoadingModal(false);
    }
  };

  // Handle User Created (Phase 9)
  const handleUserCreated = (newUserData: UserAdminCreateResponseDTO) => {
    setIsCreateModalOpen(false);
    setCredentialData(newUserData);
    setIsCredentialModalOpen(true);
    setSuccessBanner(`User @${newUserData.user.username} successfully provisioned.`);
    loadUsers();
  };

  // Close One-Time Credential Modal (Phase 9 & 10)
  const handleCloseCredentialModal = () => {
    setIsCredentialModalOpen(false);
    setCredentialData(null);
  };

  // Trigger Phase 10 Lifecycle Action
  const handleTriggerLifecycle = (action: LifecycleActionType, targetUser: UserSummaryItem | UserDetailDTO) => {
    setLifecycleAction(action);
    setLifecycleTargetUser(targetUser);
    setIsLifecycleModalOpen(true);
  };

  // Handle Successful Phase 10 Lifecycle Action
  const handleLifecycleSuccess = async (action: LifecycleActionType, result?: any) => {
    setIsLifecycleModalOpen(false);
    const target = lifecycleTargetUser;

    if (action === 'RESET_PASSWORD' && result) {
      const resetRes = result as PasswordResetResponseDTO;
      setCredentialData({
        user: {
          id: resetRes.user_id,
          username: resetRes.username,
          full_name: target?.full_name,
          email: target?.email,
        },
        temporary_password: resetRes.temporary_password,
        expires_at: resetRes.expires_at,
        title: 'Password Reset Successfully',
        message: resetRes.message,
      });
      setIsCredentialModalOpen(true);
      setSuccessBanner(`Password successfully reset for @${resetRes.username}. Previous sessions revoked.`);
    } else if (action === 'ACTIVATE') {
      setSuccessBanner(`User @${target?.username} successfully activated.`);
    } else if (action === 'DEACTIVATE') {
      setSuccessBanner(`User @${target?.username} successfully deactivated. Active sessions invalidated.`);
    } else if (action === 'DELETE') {
      setSuccessBanner(result?.message || `User @${target?.username} permanently deleted.`);
      if (selectedUser?.id === target?.id) {
        setIsModalOpen(false);
        setSelectedUser(null);
      }
    }

    setLifecycleAction(null);
    setLifecycleTargetUser(null);

    // Refresh directory & counters
    loadUsers();

    // If detail modal is open for this user, refresh detail
    if (selectedUser && target && selectedUser.id === target.id && action !== 'DELETE') {
      try {
        const updatedDetail = await adminUserService.getUserById(selectedUser.id);
        setSelectedUser(updatedDetail);
      } catch {
        // Ignore if error
      }
    }
  };

  return (
    <AppShell>
      {/* Content Wrapper */}
      <main className="page-main-container">
          {/* Header Section */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
            <div>
              <h1 style={{ fontSize: '1.4rem', fontWeight: 800, color: tokens.textPrimary, margin: '0 0 4px 0', letterSpacing: '-0.02em' }}>
                User Management Dashboard
              </h1>
              <p style={{ fontSize: '0.82rem', color: tokens.textSecondary, margin: 0 }}>
                Platform identity directory, RBAC role assignments, security status & lifecycle operations
              </p>
            </div>

            {/* Top Right Action: Create User Button */}
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setIsCreateModalOpen(true)}
                style={{
                  ...primaryButtonBase,
                  padding: '9px 18px',
                  fontSize: '0.82rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  backgroundColor: tokens.primaryAccent,
                }}
              >
                <Plus size={16} />
                <span>Create User</span>
              </button>
            </div>
          </div>

          {/* Success Banner */}
          {successBanner && (
            <div
              role="status"
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 16px',
                backgroundColor: tokens.statusSuccessBg,
                border: `1px solid ${tokens.statusSuccessBorder}`,
                borderRadius: '8px',
                color: tokens.statusSuccessText,
                fontSize: '0.82rem',
                fontWeight: 600,
                marginBottom: '18px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Check size={16} />
                <span>{successBanner}</span>
              </div>
              <button
                type="button"
                onClick={() => setSuccessBanner(null)}
                style={{ background: 'none', border: 'none', color: tokens.statusSuccessText, cursor: 'pointer', padding: '2px' }}
              >
                ✕
              </button>
            </div>
          )}

          {/* Error Alert */}
          {error && (
            <div
              role="alert"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '12px 16px',
                backgroundColor: tokens.statusErrorBg,
                border: `1px solid ${tokens.statusErrorBorder}`,
                borderRadius: '8px',
                color: tokens.statusErrorText,
                fontSize: '0.82rem',
                marginBottom: '20px',
              }}
            >
              <AlertTriangle size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* Live Metrics Summary Cards (Responsive: 4col -> 2col -> 1col) */}
          <div data-tour="admin-users-metrics" className="responsive-4col-grid" style={{ marginBottom: '24px' }}>
            {/* Card 1: Total Registered */}
            <div style={{ backgroundColor: '#FFFFFF', border: `1px solid ${tokens.border}`, borderRadius: '10px', padding: '16px 20px', boxShadow: '0 1px 3px rgba(0,0,0,0.02)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: tokens.textSecondary, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Total Registered</span>
                <div style={{ width: '32px', height: '32px', borderRadius: '6px', backgroundColor: 'rgba(79, 70, 229, 0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Users size={16} color={tokens.primaryAccent} />
                </div>
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: tokens.textPrimary, marginTop: '8px' }}>
                {isLoading ? '...' : metrics.total_users}
              </div>
              <div style={{ fontSize: '0.72rem', color: tokens.textMuted, marginTop: '4px' }}>Provisioned identities in database</div>
            </div>

            {/* Card 2: Active Accounts */}
            <div style={{ backgroundColor: '#FFFFFF', border: `1px solid ${tokens.border}`, borderRadius: '10px', padding: '16px 20px', boxShadow: '0 1px 3px rgba(0,0,0,0.02)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: tokens.textSecondary, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Active Accounts</span>
                <div style={{ width: '32px', height: '32px', borderRadius: '6px', backgroundColor: 'rgba(16, 185, 129, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <UserCheck size={16} color="#059669" />
                </div>
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#059669', marginTop: '8px' }}>
                {isLoading ? '...' : metrics.active_users}
              </div>
              <div style={{ fontSize: '0.72rem', color: tokens.textMuted, marginTop: '4px' }}>Permitted to sign in & stream data</div>
            </div>

            {/* Card 3: Administrators */}
            <div style={{ backgroundColor: '#FFFFFF', border: `1px solid ${tokens.border}`, borderRadius: '10px', padding: '16px 20px', boxShadow: '0 1px 3px rgba(0,0,0,0.02)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: tokens.textSecondary, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Administrators</span>
                <div style={{ width: '32px', height: '32px', borderRadius: '6px', backgroundColor: 'rgba(124, 58, 237, 0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Shield size={16} color="#7C3AED" />
                </div>
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#7C3AED', marginTop: '8px' }}>
                {isLoading ? '...' : metrics.administrators}
              </div>
              <div style={{ fontSize: '0.72rem', color: tokens.textMuted, marginTop: '4px' }}>SUPER_ADMIN & ADMIN authority</div>
            </div>

            {/* Card 4: Password Pending */}
            <div style={{ backgroundColor: '#FFFFFF', border: `1px solid ${tokens.border}`, borderRadius: '10px', padding: '16px 20px', boxShadow: '0 1px 3px rgba(0,0,0,0.02)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 600, color: tokens.textSecondary, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Password Pending</span>
                <div style={{ width: '32px', height: '32px', borderRadius: '6px', backgroundColor: 'rgba(245, 158, 11, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <KeyRound size={16} color="#D97706" />
                </div>
              </div>
              <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#D97706', marginTop: '8px' }}>
                {isLoading ? '...' : metrics.password_pending}
              </div>
              <div style={{ fontSize: '0.72rem', color: tokens.textMuted, marginTop: '4px' }}>Temporary credentials issued</div>
            </div>
          </div>

          <div data-tour="admin-users-table">
          {/* Search, Filter & Controls Bar */}
          <div
            style={{
              backgroundColor: '#FFFFFF',
              border: `1px solid ${tokens.border}`,
              borderRadius: '10px 10px 0 0',
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '12px',
              borderBottom: `1px solid ${tokens.border}`,
            }}
          >
            {/* Search Input */}
            <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
              <Search size={15} color="#94A3B8" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by username, full name, or email..."
                style={{
                  ...formInputStyle,
                  padding: '8px 12px 8px 36px',
                  fontSize: '0.8rem',
                  width: '100%',
                }}
              />
            </div>

            {/* Filters */}
            <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
              {/* Account Status Filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{
                  ...formInputStyle,
                  padding: '8px 12px',
                  fontSize: '0.8rem',
                  backgroundColor: '#FFFFFF',
                  cursor: 'pointer',
                  width: 'auto',
                }}
              >
                <option value="">All Account Statuses</option>
                <option value="ACTIVE">ACTIVE</option>
                <option value="INACTIVE">INACTIVE</option>
                <option value="DEACTIVATED">DEACTIVATED</option>
                <option value="LOCKED">LOCKED</option>
              </select>

              {/* Role Filter */}
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                style={{
                  ...formInputStyle,
                  padding: '8px 12px',
                  fontSize: '0.8rem',
                  backgroundColor: '#FFFFFF',
                  cursor: 'pointer',
                  width: 'auto',
                }}
              >
                <option value="">All Roles</option>
                <option value="SUPER_ADMIN">SUPER_ADMIN</option>
                <option value="ADMIN">ADMIN</option>
                <option value="QUALITY_HEAD">QUALITY_HEAD</option>
                <option value="LAB_TECHNICIAN">LAB_TECHNICIAN</option>
                <option value="PLANT_OPERATOR">PLANT_OPERATOR</option>
                <option value="ANALYST_VIEWER">ANALYST_VIEWER</option>
              </select>

              {/* Refresh Button */}
              <button
                type="button"
                onClick={loadUsers}
                disabled={isLoading}
                style={{
                  ...secondaryButtonBase,
                  padding: '8px 12px',
                  fontSize: '0.8rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
                title="Refresh user directory"
              >
                <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
                <span>Refresh</span>
              </button>
            </div>
          </div>

          {/* User Directory Table */}
          <div
            style={{
              backgroundColor: '#FFFFFF',
              border: `1px solid ${tokens.border}`,
              borderTop: 'none',
              borderRadius: '0 0 10px 10px',
              overflowX: 'auto',
              overflowY: 'hidden',
              WebkitOverflowScrolling: 'touch',
              boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
            }}
          >
            <table style={{ width: '100%', minWidth: '860px', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.82rem' }}>
              <thead>
                <tr style={{ backgroundColor: tokens.surfaceSecondary, borderBottom: `1px solid ${tokens.border}`, color: tokens.textSecondary, fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                  <th style={{ padding: '14px 20px' }}>User / Identity</th>
                  <th style={{ padding: '14px 20px' }}>Assigned Roles</th>
                  <th style={{ padding: '14px 20px' }}>Account Status</th>
                  <th style={{ padding: '14px 20px' }}>Password State</th>
                  <th style={{ padding: '14px 20px' }}>Last Login</th>
                  <th style={{ padding: '14px 20px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={6} style={{ padding: '40px', textAlign: 'center', color: tokens.textMuted }}>
                      Loading directory accounts...
                    </td>
                  </tr>
                ) : users.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ padding: '40px', textAlign: 'center', color: tokens.textMuted }}>
                      <div style={{ fontWeight: 600, color: tokens.textPrimary, marginBottom: '4px' }}>No accounts found</div>
                      <div style={{ fontSize: '0.75rem' }}>Try adjusting your search criteria or filter selections.</div>
                    </td>
                  </tr>
                ) : (
                  users.map((u, idx) => (
                    <tr
                      key={u.id}
                      style={{
                        borderBottom: idx === users.length - 1 ? 'none' : `1px solid ${tokens.borderLight}`,
                        transition: 'background-color 0.1s ease',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#F8FAFC')}
                      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#FFFFFF')}
                    >
                      {/* Identity */}
                      <td style={{ padding: '14px 20px' }}>
                        <div style={{ fontWeight: 700, color: tokens.textPrimary, fontSize: '0.85rem' }}>
                          <span>{u.full_name}</span> <span>(@{u.username})</span>
                        </div>
                        <div style={{ color: tokens.textMuted, fontSize: '0.75rem', marginTop: '1px' }}>
                          {u.email}
                        </div>
                      </td>

                      {/* Roles */}
                      <td style={{ padding: '14px 20px' }}>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                          {u.roles && u.roles.map((r) => (
                            <span
                              key={r}
                              style={{
                                fontSize: '0.68rem',
                                fontWeight: 700,
                                padding: '2px 8px',
                                borderRadius: '4px',
                                backgroundColor: r === 'SUPER_ADMIN' ? 'rgba(124, 58, 237, 0.1)' : tokens.primaryAccentLight,
                                color: r === 'SUPER_ADMIN' ? '#7C3AED' : tokens.primaryAccent,
                                border: `1px solid ${r === 'SUPER_ADMIN' ? 'rgba(124, 58, 237, 0.25)' : tokens.primaryAccentBorder}`,
                              }}
                            >
                              {r === 'SUPER_ADMIN' ? 'Superuser' : r}
                            </span>
                          ))}
                        </div>
                      </td>

                      {/* Account Status */}
                      <td style={{ padding: '14px 20px' }}>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            fontSize: '0.72rem',
                            fontWeight: 600,
                            padding: '3px 10px',
                            borderRadius: '12px',
                            backgroundColor: u.account_status === 'ACTIVE' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(220, 38, 38, 0.1)',
                            color: u.account_status === 'ACTIVE' ? '#059669' : '#DC2626',
                            border: `1px solid ${u.account_status === 'ACTIVE' ? 'rgba(16, 185, 129, 0.25)' : 'rgba(220, 38, 38, 0.25)'}`,
                          }}
                        >
                          <span
                            style={{
                              width: '6px',
                              height: '6px',
                              borderRadius: '50%',
                              backgroundColor: u.account_status === 'ACTIVE' ? '#059669' : '#DC2626',
                            }}
                          />
                          {u.account_status}
                        </span>
                      </td>

                      {/* Password State */}
                      <td style={{ padding: '14px 20px', color: tokens.textSecondary, fontSize: '0.78rem' }}>
                        <div>{u.password_status}</div>
                        {u.must_change_password && (
                          <span style={{ fontSize: '0.68rem', color: '#D97706', fontWeight: 600 }}>
                            (Must Change)
                          </span>
                        )}
                      </td>

                      {/* Last Login */}
                      <td style={{ padding: '14px 20px', color: tokens.textMuted, fontSize: '0.75rem' }}>
                        {u.last_login_at ? new Date(u.last_login_at).toLocaleString() : 'Never'}
                      </td>

                      {/* Actions Group */}
                      <td style={{ padding: '14px 20px', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', justifyContent: 'flex-end' }}>
                          {/* Inspect */}
                          <button
                            type="button"
                            onClick={() => handleInspectUser(u.id)}
                            style={{
                              padding: '5px 10px',
                              backgroundColor: '#FFFFFF',
                              border: `1px solid ${tokens.border}`,
                              borderRadius: '6px',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              color: tokens.primaryAccent,
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                            }}
                            title="Inspect user details"
                          >
                            <Eye size={13} />
                            <span>Inspect</span>
                          </button>

                          {/* Reset Password */}
                          <button
                            type="button"
                            onClick={() => handleTriggerLifecycle('RESET_PASSWORD', u)}
                            style={{
                              padding: '5px 9px',
                              backgroundColor: '#FFFBEB',
                              border: '1px solid rgba(245, 158, 11, 0.35)',
                              borderRadius: '6px',
                              fontSize: '0.75rem',
                              fontWeight: 600,
                              color: '#B45309',
                              cursor: 'pointer',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '4px',
                            }}
                            title="Reset password"
                          >
                            <KeyRound size={13} />
                            <span>Reset</span>
                          </button>

                          {/* Activate / Deactivate */}
                          {u.account_status === 'ACTIVE' ? (
                            <button
                              type="button"
                              onClick={() => handleTriggerLifecycle('DEACTIVATE', u)}
                              style={{
                                padding: '5px 9px',
                                backgroundColor: '#FEF2F2',
                                border: '1px solid rgba(239, 68, 68, 0.35)',
                                borderRadius: '6px',
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                color: '#B91C1C',
                                cursor: 'pointer',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                              }}
                              title="Deactivate account"
                            >
                              <UserX size={13} />
                              <span>Deactivate</span>
                            </button>
                          ) : (
                            <button
                              type="button"
                              onClick={() => handleTriggerLifecycle('ACTIVATE', u)}
                              style={{
                                padding: '5px 9px',
                                backgroundColor: '#ECFDF5',
                                border: '1px solid rgba(16, 185, 129, 0.35)',
                                borderRadius: '6px',
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                color: '#047857',
                                cursor: 'pointer',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                              }}
                              title="Activate account"
                            >
                              <CheckCircle2 size={13} />
                              <span>Activate</span>
                            </button>
                          )}

                          {/* Delete User (SUPER_ADMIN only) */}
                          {isSuperAdmin && (
                            <button
                              type="button"
                              onClick={() => handleTriggerLifecycle('DELETE', u)}
                              style={{
                                padding: '5px 8px',
                                backgroundColor: '#FFFFFF',
                                border: '1px solid rgba(220, 38, 38, 0.3)',
                                borderRadius: '6px',
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                color: '#DC2626',
                                cursor: 'pointer',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '4px',
                              }}
                              title="Delete user"
                            >
                              <Trash2 size={13} />
                              <span>Delete</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>

            {/* Table Footer */}
            <div
              style={{
                padding: '14px 20px',
                backgroundColor: tokens.surfaceSecondary,
                borderTop: `1px solid ${tokens.border}`,
                fontSize: '0.75rem',
                color: tokens.textMuted,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span>Showing {users.length} registered accounts</span>
              <span style={{ fontSize: '0.7rem' }}>Authoritative Database Sync Active</span>
            </div>
          </div>
        
        </div>

        {/* Account Overview Modal */}
        <UserDetailModal
          user={selectedUser}
          isOpen={isModalOpen}
          onClose={() => {
            setIsModalOpen(false);
            setSelectedUser(null);
          }}
          isLoading={isLoadingModal}
          onTriggerLifecycleAction={handleTriggerLifecycle}
          isSuperAdmin={isSuperAdmin}
        />

        {/* Phase 9 Create User Modal */}
        <CreateUserModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onSuccess={handleUserCreated}
        />

        {/* Phase 9 & 10 One-Time Credential Modal */}
        <OneTimeCredentialModal
          credentialData={credentialData}
          isOpen={isCredentialModalOpen}
          onClose={handleCloseCredentialModal}
        />

        {/* Phase 10 Lifecycle Action Confirmation Modal */}
        <UserLifecycleActionModal
          isOpen={isLifecycleModalOpen}
          actionType={lifecycleAction}
          targetUser={lifecycleTargetUser}
          onClose={() => {
            setIsLifecycleModalOpen(false);
            setLifecycleAction(null);
            setLifecycleTargetUser(null);
          }}
          onSuccess={handleLifecycleSuccess}
        />
      </main>
    </AppShell>
  );
};
