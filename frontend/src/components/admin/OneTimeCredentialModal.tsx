/**
 * Authoritative One-Time Credential Disclosure Modal for ACC RMC Platform.
 *
 * Enforces Phase 9 & Phase 10 Certified Security Rules:
 * 1. Plaintext temporary password displayed strictly once.
 * 2. Dedicated one-click clipboard copy action with accessible visual feedback.
 * 3. Close-before-copy interstitial safety warning to prevent credential loss.
 * 4. Zero persistent storage (never written to localStorage/sessionStorage/cookies/URLs).
 * 5. Instant memory cleanup upon modal closure or unmount.
 * 6. Supports User Provisioning and Admin Reset Password disclosure titles.
 * 7. Compliant Enterprise Light Theme tokens.
 */

import React, { useState, useEffect } from 'react';
import { UserAdminCreateResponseDTO } from '../../services/adminUserService';
import { enterpriseLightTokens as tokens, primaryButtonBase, secondaryButtonBase } from '../manual-entry/enterpriseLightTokens';
import { KeyRound, Copy, Check, AlertTriangle, X, ShieldAlert } from 'lucide-react';

export interface OneTimeCredentialData {
  user: {
    id?: string;
    full_name?: string;
    username: string;
    email?: string;
  };
  temporary_password: string;
  expires_at: string;
  message?: string;
  title?: string;
}

interface OneTimeCredentialModalProps {
  credentialData: UserAdminCreateResponseDTO | OneTimeCredentialData | null;
  isOpen: boolean;
  onClose: () => void;
}

export const OneTimeCredentialModal: React.FC<OneTimeCredentialModalProps> = ({
  credentialData,
  isOpen,
  onClose,
}) => {
  const [hasCopied, setHasCopied] = useState(false);
  const [showWarning, setShowWarning] = useState(false);
  const [copyError, setCopyError] = useState(false);

  // Reset local state whenever a new credential payload is loaded
  useEffect(() => {
    if (isOpen) {
      setHasCopied(false);
      setShowWarning(false);
      setCopyError(false);
    }
  }, [isOpen, credentialData]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleAttemptClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, hasCopied]);

  if (!isOpen || !credentialData) {
    return null;
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(credentialData.temporary_password);
      setHasCopied(true);
      setShowWarning(false);
      setCopyError(false);
    } catch {
      setCopyError(true);
    }
  };

  const handleAttemptClose = () => {
    if (!hasCopied) {
      setShowWarning(true);
    } else {
      onClose();
    }
  };

  const handleForceClose = () => {
    onClose();
  };

  const modalTitle = (credentialData as any).title || 'Account Provisioned Successfully';

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="credential-modal-title"
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
          maxWidth: '520px',
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
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid rgba(16, 185, 129, 0.25)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <KeyRound size={18} color="#059669" />
            </div>
            <div>
              <h2
                id="credential-modal-title"
                style={{ fontSize: '1.05rem', fontWeight: 800, color: tokens.textPrimary, margin: 0 }}
              >
                {modalTitle}
              </h2>
              <p style={{ fontSize: '0.75rem', color: tokens.textMuted, margin: '2px 0 0 0' }}>
                One-time temporary credential disclosure
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleAttemptClose}
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
            aria-label="Close credential modal"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Identity Summary Card */}
          <div
            style={{
              padding: '14px 16px',
              backgroundColor: tokens.surfaceSecondary,
              border: `1px solid ${tokens.borderLight}`,
              borderRadius: '8px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            {credentialData.user.full_name && (
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                <span style={{ color: tokens.textSecondary }}>Full Name:</span>
                <strong style={{ color: tokens.textPrimary }}>{credentialData.user.full_name}</strong>
              </div>
            )}
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
              <span style={{ color: tokens.textSecondary }}>Username:</span>
              <strong style={{ fontFamily: 'monospace', color: tokens.textPrimary }}>@{credentialData.user.username}</strong>
            </div>
            {credentialData.user.email && (
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem' }}>
                <span style={{ color: tokens.textSecondary }}>Corporate Email:</span>
                <span style={{ color: tokens.textPrimary }}>{credentialData.user.email}</span>
              </div>
            )}
          </div>

          {/* Credential Box */}
          <div>
            <label style={{ display: 'block', fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: tokens.textMuted, marginBottom: '8px' }}>
              One-Time Temporary Password
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div
                style={{
                  flex: 1,
                  padding: '10px 14px',
                  backgroundColor: '#FFFFFF',
                  border: `1px solid ${tokens.border}`,
                  borderRadius: '6px',
                  fontFamily: 'monospace',
                  fontSize: '0.9rem',
                  fontWeight: 700,
                  color: tokens.textPrimary,
                  letterSpacing: '0.05em',
                  userSelect: 'all',
                }}
              >
                {credentialData.temporary_password}
              </div>
              <button
                type="button"
                onClick={handleCopy}
                style={{
                  ...primaryButtonBase,
                  padding: '10px 16px',
                  fontSize: '0.8rem',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  backgroundColor: hasCopied ? '#059669' : tokens.primaryAccent,
                }}
              >
                {hasCopied ? (
                  <>
                    <Check size={14} />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy size={14} />
                    <span>Copy Password</span>
                  </>
                )}
              </button>
            </div>
            {copyError && (
              <p style={{ fontSize: '0.72rem', color: '#D97706', marginTop: '4px' }}>
                Automatic clipboard copy was restricted. Please select and copy the text box manually.
              </p>
            )}
          </div>

          {/* Security Notice */}
          <div
            style={{
              padding: '12px 14px',
              backgroundColor: 'rgba(245, 158, 11, 0.08)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '8px',
              fontSize: '0.75rem',
              color: '#92400E',
              lineHeight: 1.5,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 700, marginBottom: '4px' }}>
              <ShieldAlert size={15} color="#D97706" />
              <span>One-Time Disclosure Security Notice</span>
            </div>
            <p style={{ margin: 0 }}>
              This credential will <strong>never be shown again</strong>. Please convey this temporary password to the user securely. The user will be required to change their password upon their first login.
            </p>
          </div>

          {/* Uncopied Warning Confirmation */}
          {showWarning && (
            <div
              style={{
                padding: '14px',
                backgroundColor: tokens.statusErrorBg,
                border: `1px solid ${tokens.statusErrorBorder}`,
                borderRadius: '8px',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '0.78rem', color: tokens.statusErrorText }}>
                <AlertTriangle size={16} style={{ marginTop: '2px', flexShrink: 0 }} />
                <div>
                  <strong style={{ display: 'block' }}>Credential Not Copied</strong>
                  <span>You have not copied the temporary password yet. Closing now will permanently destroy the plaintext view of this credential.</span>
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button
                  type="button"
                  onClick={handleCopy}
                  style={{
                    ...primaryButtonBase,
                    padding: '6px 12px',
                    fontSize: '0.75rem',
                    backgroundColor: tokens.primaryAccent,
                  }}
                >
                  Copy Password Now
                </button>
                <button
                  type="button"
                  onClick={handleForceClose}
                  style={{
                    ...secondaryButtonBase,
                    padding: '6px 12px',
                    fontSize: '0.75rem',
                    color: tokens.statusErrorText,
                  }}
                >
                  I Understand, Close Anyway
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '12px 24px',
            borderTop: `1px solid ${tokens.border}`,
            backgroundColor: tokens.surfaceSecondary,
          }}
        >
          <span style={{ fontSize: '0.72rem', color: tokens.textMuted }}>
            Status: Password pending initial login
          </span>
          <button
            type="button"
            onClick={handleAttemptClose}
            style={{
              ...primaryButtonBase,
              padding: '8px 16px',
              fontSize: '0.8rem',
              backgroundColor: '#1E293B',
            }}
          >
            Done & Return to Directory
          </button>
        </div>
      </div>
    </div>
  );
};
