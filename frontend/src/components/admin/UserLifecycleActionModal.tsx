/**
 * Authoritative User Lifecycle Action Confirmation Modal for ACC RMC Platform (Phase 10).
 *
 * Implements:
 * 1. Reset Password: Confirmation dialog explaining 72h temporary password & session invalidation.
 * 2. Activate User: Confirmation dialog for activating inactive/deactivated/locked accounts.
 * 3. Deactivate User: Confirmation dialog explaining immediate token invalidation.
 * 4. Delete User: Destructive action confirmation requiring exact username entry to confirm.
 * 5. Duplicate Submission Guard: Disables buttons and shows loading indicator while request is in flight.
 * 6. Enterprise Light Theme tokens & accessible dialog markup (`role="dialog"`).
 */

import React, { useState, useEffect } from 'react';
import { UserSummaryItem, UserDetailDTO, adminUserService, PasswordResetResponseDTO } from '../../services/adminUserService';
import { enterpriseLightTokens as tokens, primaryButtonBase, secondaryButtonBase, formInputStyle } from '../manual-entry/enterpriseLightTokens';
import { KeyRound, CheckCircle2, UserX, Trash2, AlertTriangle, X, ShieldAlert } from 'lucide-react';

export type LifecycleActionType = 'RESET_PASSWORD' | 'ACTIVATE' | 'DEACTIVATE' | 'DELETE';

interface UserLifecycleActionModalProps {
  isOpen: boolean;
  actionType: LifecycleActionType | null;
  targetUser: UserSummaryItem | UserDetailDTO | null;
  onClose: () => void;
  onSuccess: (action: LifecycleActionType, result?: any) => void;
}

export const UserLifecycleActionModal: React.FC<UserLifecycleActionModalProps> = ({
  isOpen,
  actionType,
  targetUser,
  onClose,
  onSuccess,
}) => {
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setDeleteConfirmText('');
      setIsSubmitting(false);
      setErrorMessage(null);
    }
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !isSubmitting && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, actionType, targetUser, isSubmitting, onClose]);

  if (!isOpen || !actionType || !targetUser) {
    return null;
  }

  const isDelete = actionType === 'DELETE';
  const isDeleteConfirmed = isDelete && deleteConfirmText.trim() === targetUser.username;

  const handleConfirm = async () => {
    if (isDelete && !isDeleteConfirmed) return;

    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      if (actionType === 'RESET_PASSWORD') {
        const res: PasswordResetResponseDTO = await adminUserService.resetPassword(targetUser.id);
        onSuccess('RESET_PASSWORD', res);
      } else if (actionType === 'ACTIVATE') {
        const res = await adminUserService.activateUser(targetUser.id);
        onSuccess('ACTIVATE', res);
      } else if (actionType === 'DEACTIVATE') {
        const res = await adminUserService.deactivateUser(targetUser.id);
        onSuccess('DEACTIVATE', res);
      } else if (actionType === 'DELETE') {
        const res = await adminUserService.deleteUser(targetUser.id);
        onSuccess('DELETE', res);
      }
    } catch (err: any) {
      const detail = err?.data?.detail || err?.message || 'Operation failed. Please verify user state and try again.';
      setErrorMessage(typeof detail === 'string' ? detail : JSON.stringify(detail));
    } finally {
      setIsSubmitting(false);
    }
  };

  const getActionConfig = () => {
    switch (actionType) {
      case 'RESET_PASSWORD':
        return {
          icon: <KeyRound size={20} color="#D97706" />,
          iconBg: 'rgba(245, 158, 11, 0.1)',
          iconBorder: 'rgba(245, 158, 11, 0.25)',
          title: 'Reset User Password',
          confirmBtnText: isSubmitting ? 'Resetting Password...' : 'Confirm Password Reset',
          confirmBtnBg: tokens.primaryAccent,
          confirmBtnColor: '#FFFFFF',
          description: `You are about to reset the password for ${targetUser.full_name} (@${targetUser.username}).`,
          notice: 'This will immediately revoke all active sessions and issue a new cryptographically random 14-character temporary password valid for 72 hours. The user will be required to change their password on next sign in.',
        };
      case 'ACTIVATE':
        return {
          icon: <CheckCircle2 size={20} color="#059669" />,
          iconBg: 'rgba(16, 185, 129, 0.1)',
          iconBorder: 'rgba(16, 185, 129, 0.25)',
          title: 'Activate User Account',
          confirmBtnText: isSubmitting ? 'Activating Account...' : 'Activate Account',
          confirmBtnBg: '#059669',
          confirmBtnColor: '#FFFFFF',
          description: `Activate access for ${targetUser.full_name} (@${targetUser.username}).`,
          notice: 'The user account status will be set to ACTIVE, allowing the user to authenticate into the ACC RMC Operations Platform using their assigned credentials.',
        };
      case 'DEACTIVATE':
        return {
          icon: <UserX size={20} color="#DC2626" />,
          iconBg: 'rgba(220, 38, 38, 0.1)',
          iconBorder: 'rgba(220, 38, 38, 0.25)',
          title: 'Deactivate User Account',
          confirmBtnText: isSubmitting ? 'Deactivating Account...' : 'Deactivate Account',
          confirmBtnBg: '#DC2626',
          confirmBtnColor: '#FFFFFF',
          description: `Deactivate access for ${targetUser.full_name} (@${targetUser.username}).`,
          notice: 'This will immediately invalidate all active login tokens and prevent this user from signing in until an administrator reactivates the account.',
        };
      case 'DELETE':
        return {
          icon: <Trash2 size={20} color="#DC2626" />,
          iconBg: 'rgba(220, 38, 38, 0.1)',
          iconBorder: 'rgba(220, 38, 38, 0.25)',
          title: 'Permanently Delete User Account',
          confirmBtnText: isSubmitting ? 'Deleting Account...' : 'Permanently Delete User',
          confirmBtnBg: '#DC2626',
          confirmBtnColor: '#FFFFFF',
          description: `You are about to permanently delete the account for ${targetUser.full_name} (@${targetUser.username}).`,
          notice: 'WARNING: This action is destructive and irreversible. User record and role assignments will be removed. Security audit logs will be permanently retained with unlinked references for regulatory compliance.',
        };
    }
  };

  const config = getActionConfig();

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="lifecycle-modal-title"
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
        zIndex: 60,
        padding: '20px',
        fontFamily: tokens.fontFamily,
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '480px',
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
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 20px',
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
                backgroundColor: config.iconBg,
                border: `1px solid ${config.iconBorder}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {config.icon}
            </div>
            <div>
              <h2
                id="lifecycle-modal-title"
                style={{ fontSize: '1rem', fontWeight: 800, color: tokens.textPrimary, margin: 0 }}
              >
                {config.title}
              </h2>
              <p style={{ fontSize: '0.75rem', color: tokens.textMuted, margin: '1px 0 0 0' }}>
                Governance & Lifecycle Action
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
              color: tokens.textSecondary,
              padding: '6px',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
            aria-label="Close action modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Target Identity Box */}
          <div
            style={{
              padding: '12px 14px',
              backgroundColor: tokens.surfaceSecondary,
              border: `1px solid ${tokens.borderLight}`,
              borderRadius: '8px',
              fontSize: '0.8rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: tokens.textSecondary }}>Target User:</span>
              <strong style={{ color: tokens.textPrimary }}>{targetUser.full_name}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: tokens.textSecondary }}>Username:</span>
              <span style={{ fontFamily: 'monospace', color: tokens.textPrimary }}>@{targetUser.username}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: tokens.textSecondary }}>Current Status:</span>
              <span style={{ fontWeight: 600, color: targetUser.account_status === 'ACTIVE' ? '#059669' : '#DC2626' }}>
                {targetUser.account_status}
              </span>
            </div>
          </div>

          {/* Description & Notice */}
          <div
            style={{
              padding: '12px 14px',
              backgroundColor: isDelete ? 'rgba(220, 38, 38, 0.05)' : actionType === 'RESET_PASSWORD' ? 'rgba(245, 158, 11, 0.06)' : tokens.surfaceSecondary,
              border: `1px solid ${isDelete ? 'rgba(220, 38, 38, 0.25)' : actionType === 'RESET_PASSWORD' ? 'rgba(245, 158, 11, 0.25)' : tokens.borderLight}`,
              borderRadius: '8px',
              fontSize: '0.76rem',
              lineHeight: 1.5,
              color: isDelete ? '#991B1B' : tokens.textSecondary,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, marginBottom: '4px' }}>
              {isDelete ? <AlertTriangle size={14} color="#DC2626" /> : <ShieldAlert size={14} color="#64748B" />}
              <span>Policy Notice</span>
            </div>
            <p style={{ margin: 0 }}>{config.notice}</p>
          </div>

          {/* Type-to-Confirm Input for Delete */}
          {isDelete && (
            <div>
              <label
                htmlFor="confirm-delete-input"
                style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: tokens.textPrimary, marginBottom: '6px' }}
              >
                Type <span style={{ fontFamily: 'monospace', color: '#DC2626' }}>{targetUser.username}</span> to confirm permanent deletion:
              </label>
              <input
                id="confirm-delete-input"
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder={targetUser.username}
                disabled={isSubmitting}
                autoComplete="off"
                style={{
                  ...formInputStyle,
                  borderColor: deleteConfirmText && !isDeleteConfirmed ? '#DC2626' : tokens.border,
                }}
              />
            </div>
          )}

          {/* Error Message */}
          {errorMessage && (
            <div
              role="alert"
              style={{
                padding: '10px 12px',
                backgroundColor: tokens.statusErrorBg,
                border: `1px solid ${tokens.statusErrorBorder}`,
                borderRadius: '6px',
                color: tokens.statusErrorText,
                fontSize: '0.78rem',
                lineHeight: 1.4,
                display: 'flex',
                alignItems: 'flex-start',
                gap: '6px',
              }}
            >
              <AlertTriangle size={15} style={{ marginTop: '2px', flexShrink: 0 }} />
              <div>{errorMessage}</div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: '10px',
            padding: '12px 20px',
            borderTop: `1px solid ${tokens.border}`,
            backgroundColor: tokens.surfaceSecondary,
          }}
        >
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            style={secondaryButtonBase}
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={isSubmitting || (isDelete && !isDeleteConfirmed)}
            style={{
              ...primaryButtonBase,
              padding: '8px 16px',
              fontSize: '0.8rem',
              backgroundColor: config.confirmBtnBg,
              color: config.confirmBtnColor,
              opacity: isSubmitting || (isDelete && !isDeleteConfirmed) ? 0.6 : 1,
              cursor: isSubmitting || (isDelete && !isDeleteConfirmed) ? 'not-allowed' : 'pointer',
            }}
          >
            {config.confirmBtnText}
          </button>
        </div>
      </div>
    </div>
  );
};
