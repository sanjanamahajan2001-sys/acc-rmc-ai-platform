import React, { useEffect } from 'react';
import { UserDetailDTO } from '../../services/adminUserService';
import { enterpriseLightTokens as tokens, secondaryButtonBase, primaryButtonBase } from '../manual-entry/enterpriseLightTokens';
import { X, User, Shield, Lock, Clock, KeyRound, CheckCircle2, UserX, Trash2 } from 'lucide-react';
import { LifecycleActionType } from './UserLifecycleActionModal';

interface UserDetailModalProps {
  user: UserDetailDTO | null;
  isOpen: boolean;
  onClose: () => void;
  isLoading?: boolean;
  onTriggerLifecycleAction?: (actionType: LifecycleActionType, user: UserDetailDTO) => void;
  isSuperAdmin?: boolean;
}

export const UserDetailModal: React.FC<UserDetailModalProps> = ({
  user,
  isOpen,
  onClose,
  isLoading = false,
  onTriggerLifecycleAction,
  isSuperAdmin = false,
}) => {
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="user-detail-modal-title"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.45)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50,
        padding: '20px',
        fontFamily: tokens.fontFamily,
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '680px',
          maxHeight: '90vh',
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          border: `1px solid ${tokens.border}`,
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        {/* Modal Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 24px',
            borderBottom: `1px solid ${tokens.border}`,
            backgroundColor: '#FFFFFF',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                backgroundColor: tokens.primaryAccentLight,
                border: `1px solid ${tokens.primaryAccentBorder}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <User size={18} color={tokens.primaryAccent} />
            </div>
            <div>
              <h2
                id="user-detail-modal-title"
                style={{ fontSize: '1.05rem', fontWeight: 800, color: tokens.textPrimary, margin: 0 }}
              >
                User Account Overview
              </h2>
              <p style={{ fontSize: '0.75rem', color: tokens.textMuted, margin: '2px 0 0 0' }}>
                Identity inspection & security governance
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: tokens.textSecondary,
              padding: '6px',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            aria-label="Close overview modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {isLoading || !user ? (
            <div style={{ padding: '40px 0', textAlign: 'center', color: tokens.textMuted }}>
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  border: `3px solid ${tokens.border}`,
                  borderTopColor: tokens.primaryAccent,
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite',
                  margin: '0 auto 12px auto',
                }}
              />
              <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
              <span style={{ fontSize: '0.85rem' }}>Loading user details from database...</span>
            </div>
          ) : (
            <>
              {/* Primary Identity Banner */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '16px 20px',
                  backgroundColor: tokens.surfaceSecondary,
                  border: `1px solid ${tokens.border}`,
                  borderRadius: '8px',
                }}
              >
                <div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: tokens.textPrimary }}>
                    {user.full_name}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: tokens.textSecondary, marginTop: '2px' }}>
                    <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>@{user.username}</span> • {user.email}
                  </div>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      padding: '4px 12px',
                      borderRadius: '12px',
                      backgroundColor: user.account_status === 'ACTIVE' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(220, 38, 38, 0.1)',
                      color: user.account_status === 'ACTIVE' ? '#059669' : '#DC2626',
                      border: `1px solid ${user.account_status === 'ACTIVE' ? 'rgba(16, 185, 129, 0.25)' : 'rgba(220, 38, 38, 0.25)'}`,
                    }}
                  >
                    <span
                      style={{
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        backgroundColor: user.account_status === 'ACTIVE' ? '#059669' : '#DC2626',
                      }}
                    />
                    {user.account_status}
                  </span>
                  <span style={{ fontSize: '0.68rem', fontFamily: 'monospace', color: tokens.textMuted }}>
                    ID: {user.id ? `${user.id.substring(0, 8)}...` : 'N/A'}
                  </span>
                </div>
              </div>

              {/* Roles Section */}
              <div>
                <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: tokens.textMuted, marginBottom: '8px' }}>
                  Assigned RBAC Roles
                </label>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {user.roles && user.roles.length > 0 ? (
                    user.roles.map((role: string) => (
                      <span
                        key={role}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '5px 10px',
                          borderRadius: '6px',
                          backgroundColor: role === 'SUPER_ADMIN' ? 'rgba(124, 58, 237, 0.1)' : tokens.primaryAccentLight,
                          color: role === 'SUPER_ADMIN' ? '#7C3AED' : tokens.primaryAccent,
                          border: `1px solid ${role === 'SUPER_ADMIN' ? 'rgba(124, 58, 237, 0.25)' : tokens.primaryAccentBorder}`,
                          fontSize: '0.75rem',
                          fontWeight: 600,
                        }}
                      >
                        <Shield size={13} />
                        {role === 'SUPER_ADMIN' ? 'SUPER_ADMIN (Superuser)' : role}
                      </span>
                    ))
                  ) : (
                    <span style={{ fontSize: '0.78rem', color: tokens.textMuted, fontStyle: 'italic' }}>No active roles assigned</span>
                  )}
                </div>
              </div>

              {/* Account Security & Password Status Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px' }}>
                <div
                  style={{
                    padding: '14px 16px',
                    borderRadius: '8px',
                    border: `1px solid ${tokens.border}`,
                    backgroundColor: tokens.surfaceSecondary,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', fontWeight: 700, color: tokens.textPrimary, marginBottom: '12px' }}>
                    <Lock size={14} color={tokens.primaryAccent} />
                    Authentication State
                  </div>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.78rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '6px', borderBottom: `1px solid ${tokens.borderLight}` }}>
                      <span style={{ color: tokens.textSecondary }}>Password Status:</span>
                      <span style={{ fontWeight: 600, color: tokens.textPrimary, backgroundColor: '#FFFFFF', padding: '2px 6px', borderRadius: '4px', border: `1px solid ${tokens.borderLight}` }}>
                        {user.password_status}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '6px', borderBottom: `1px solid ${tokens.borderLight}` }}>
                      <span style={{ color: tokens.textSecondary }}>Must Change:</span>
                      <span style={{ fontWeight: 600, color: user.must_change_password ? '#D97706' : '#059669' }}>
                        {user.must_change_password ? 'Yes (Pending)' : 'No'}
                      </span>
                    </div>
                    {user.failed_login_attempts !== undefined && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: tokens.textSecondary }}>Failed Attempts:</span>
                        <span style={{ fontWeight: 600, color: tokens.textPrimary }}>{user.failed_login_attempts}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div
                  style={{
                    padding: '14px 16px',
                    borderRadius: '8px',
                    border: `1px solid ${tokens.border}`,
                    backgroundColor: tokens.surfaceSecondary,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.78rem', fontWeight: 700, color: tokens.textPrimary, marginBottom: '12px' }}>
                    <Clock size={14} color={tokens.primaryAccent} />
                    Access & Lifecycle Audit
                  </div>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.78rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '6px', borderBottom: `1px solid ${tokens.borderLight}` }}>
                      <span style={{ color: tokens.textSecondary }}>Last Login:</span>
                      <span style={{ fontWeight: 600, color: tokens.textPrimary }}>
                        {user.last_login_at ? new Date(user.last_login_at).toLocaleString() : 'Never logged in'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '6px', borderBottom: `1px solid ${tokens.borderLight}` }}>
                      <span style={{ color: tokens.textSecondary }}>Created:</span>
                      <span style={{ fontWeight: 600, color: tokens.textPrimary }}>
                        {user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ color: tokens.textSecondary }}>Record Version:</span>
                      <span style={{ fontFamily: 'monospace', color: tokens.textMuted }}>v{user.version}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Security Governance Notice */}
              <div
                style={{
                  padding: '12px 14px',
                  backgroundColor: '#F8FAFC',
                  border: `1px solid ${tokens.borderLight}`,
                  borderRadius: '8px',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '10px',
                  fontSize: '0.75rem',
                  color: tokens.textSecondary,
                  lineHeight: 1.5,
                }}
              >
                <Shield size={15} color="#64748B" style={{ marginTop: '2px', flexShrink: 0 }} />
                <div>
                  <strong style={{ color: tokens.textPrimary }}>Security Governance:</strong> Passwords and encryption keys are protected under multi-layer one-way salting and hashing protocols. System administrators cannot read plaintext credentials.
                </div>
              </div>
            </>
          )}
        </div>

        {/* Modal Footer with Lifecycle Actions */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 24px',
            borderTop: `1px solid ${tokens.border}`,
            backgroundColor: tokens.surfaceSecondary,
            gap: '8px',
            flexWrap: 'wrap',
          }}
        >
          {user && onTriggerLifecycleAction ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              {/* Reset Password */}
              <button
                type="button"
                onClick={() => onTriggerLifecycleAction('RESET_PASSWORD', user)}
                style={{
                  ...secondaryButtonBase,
                  padding: '6px 12px',
                  fontSize: '0.75rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '5px',
                  color: '#B45309',
                  borderColor: 'rgba(245, 158, 11, 0.4)',
                  backgroundColor: '#FFFBEB',
                }}
              >
                <KeyRound size={13} />
                <span>Reset Password</span>
              </button>

              {/* Activate / Deactivate */}
              {user.account_status === 'ACTIVE' ? (
                <button
                  type="button"
                  onClick={() => onTriggerLifecycleAction('DEACTIVATE', user)}
                  style={{
                    ...secondaryButtonBase,
                    padding: '6px 12px',
                    fontSize: '0.75rem',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '5px',
                    color: '#B91C1C',
                    borderColor: 'rgba(239, 68, 68, 0.4)',
                    backgroundColor: '#FEF2F2',
                  }}
                >
                  <UserX size={13} />
                  <span>Deactivate</span>
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => onTriggerLifecycleAction('ACTIVATE', user)}
                  style={{
                    ...secondaryButtonBase,
                    padding: '6px 12px',
                    fontSize: '0.75rem',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '5px',
                    color: '#047857',
                    borderColor: 'rgba(16, 185, 129, 0.4)',
                    backgroundColor: '#ECFDF5',
                  }}
                >
                  <CheckCircle2 size={13} />
                  <span>Activate</span>
                </button>
              )}

              {/* Delete User (SUPER_ADMIN only) */}
              {isSuperAdmin && (
                <button
                  type="button"
                  onClick={() => onTriggerLifecycleAction('DELETE', user)}
                  style={{
                    ...secondaryButtonBase,
                    padding: '6px 12px',
                    fontSize: '0.75rem',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '5px',
                    color: '#DC2626',
                    borderColor: 'rgba(220, 38, 38, 0.3)',
                    backgroundColor: '#FFFFFF',
                  }}
                >
                  <Trash2 size={13} />
                  <span>Delete</span>
                </button>
              )}
            </div>
          ) : (
            <div />
          )}

          <button
            type="button"
            onClick={onClose}
            style={secondaryButtonBase}
          >
            Close Overview
          </button>
        </div>
      </div>
    </div>
  );
};
