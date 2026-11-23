import React, { useState, useEffect } from 'react';
import { adminUserService, UserAdminCreateRequestDTO, UserAdminCreateResponseDTO } from '../../services/adminUserService';
import { useAuth } from '../../context/AuthContext';
import { UserPlus, Shield, X, Mail, AtSign, User, AlertCircle, Check } from 'lucide-react';
import { enterpriseLightTokens as tokens, primaryButtonBase, secondaryButtonBase } from '../manual-entry/enterpriseLightTokens';

interface CreateUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (response: UserAdminCreateResponseDTO) => void;
}

export const CreateUserModal: React.FC<CreateUserModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const { isSuperAdmin } = useAuth();
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [selectedRoles, setSelectedRoles] = useState<string[]>(['PLANT_OPERATOR']);
  
  const [isLoading, setIsLoading] = useState(false);
  const [formErrors, setFormErrors] = useState<{ [key: string]: string }>({});
  const [serverError, setServerError] = useState<string | null>(null);

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

  const assignableRoles = isSuperAdmin
    ? ['SUPER_ADMIN', 'ADMIN', 'QUALITY_HEAD', 'LAB_TECHNICIAN', 'PLANT_OPERATOR', 'ANALYST_VIEWER']
    : ['ADMIN', 'QUALITY_HEAD', 'LAB_TECHNICIAN', 'PLANT_OPERATOR', 'ANALYST_VIEWER'];

  const validate = (): boolean => {
    const errors: { [key: string]: string } = {};

    if (!fullName.trim()) {
      errors.fullName = 'Full name is required.';
    }

    if (!username.trim()) {
      errors.username = 'Username is required.';
    } else if (username.length < 3) {
      errors.username = 'Username must be at least 3 characters.';
    } else if (!/^[a-zA-Z0-9_-]+$/.test(username)) {
      errors.username = 'Username can only contain alphanumeric characters, underscores, and hyphens.';
    }

    if (!email.trim()) {
      errors.email = 'Corporate email address is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = 'Please provide a valid email address.';
    }

    if (selectedRoles.length === 0) {
      errors.roles = 'At least one role must be assigned.';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleRoleToggle = (role: string) => {
    if (selectedRoles.includes(role)) {
      setSelectedRoles(selectedRoles.filter((r) => r !== role));
    } else {
      setSelectedRoles([...selectedRoles, role]);
    }
  };

  const handleSubmit = async (e?: React.FormEvent | React.MouseEvent) => {
    if (e) {
      e.preventDefault();
    }
    setServerError(null);

    if (!validate()) {
      return;
    }

    setIsLoading(true);

    try {
      const payload: UserAdminCreateRequestDTO = {
        full_name: fullName.trim(),
        username: username.trim(),
        email: email.trim().toLowerCase(),
        roles: selectedRoles,
      };

      const result = await adminUserService.createUser(payload);
      
      // Reset form
      setFullName('');
      setUsername('');
      setEmail('');
      setSelectedRoles(['PLANT_OPERATOR']);
      setFormErrors({});

      onSuccess(result);
    } catch (err: any) {
      const detailMsg = err?.response?.data?.detail;
      if (typeof detailMsg === 'string') {
        setServerError(detailMsg);
      } else if (err?.message) {
        setServerError(err.message);
      } else {
        setServerError('Failed to create user. Please verify user inputs and try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-user-modal-title"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.55)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '20px',
        fontFamily: tokens.fontFamily,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          width: '100%',
          maxWidth: '560px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1)',
          border: `1px solid ${tokens.border}`,
          overflow: 'hidden',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 24px',
            borderBottom: `1px solid ${tokens.border}`,
            backgroundColor: '#FAFCFF',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                backgroundColor: tokens.primaryAccentLight,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: tokens.primaryAccent,
              }}
            >
              <UserPlus size={18} />
            </div>
            <div>
              <h2 id="create-user-modal-title" style={{ fontSize: '1rem', fontWeight: 800, margin: 0, color: tokens.textPrimary }}>
                Create User Account
              </h2>
              <p style={{ fontSize: '0.75rem', color: tokens.textMuted, margin: '2px 0 0 0' }}>
                Enterprise identity provisioning and RBAC governance
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isLoading}
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
          >
            <X size={18} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Server Error Alert */}
            {serverError && (
              <div
                style={{
                  padding: '12px 14px',
                  backgroundColor: tokens.statusErrorBg,
                  border: `1px solid ${tokens.statusErrorBorder}`,
                  borderRadius: '8px',
                  color: tokens.statusErrorText,
                  fontSize: '0.8rem',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '8px',
                }}
              >
                <AlertCircle size={16} style={{ marginTop: '2px', flexShrink: 0 }} />
                <div>
                  <strong style={{ display: 'block' }}>Creation Error</strong>
                  <span>{serverError}</span>
                </div>
              </div>
            )}

            {/* Full Name */}
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: tokens.textPrimary, marginBottom: '6px' }}>
                Full Name <span style={{ color: tokens.statusErrorText }}>*</span>
              </label>
              <div style={{ position: 'relative' }}>
                <User size={15} color="#94A3B8" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Ramesh Sharma"
                  style={{
                    width: '100%',
                    padding: '9px 12px 9px 36px',
                    borderRadius: '6px',
                    border: `1px solid ${formErrors.fullName ? tokens.statusErrorBorder : tokens.border}`,
                    fontSize: '0.82rem',
                    color: tokens.textPrimary,
                    outline: 'none',
                    boxSizing: 'border-box',
                    backgroundColor: formErrors.fullName ? 'rgba(239, 68, 68, 0.05)' : '#FFFFFF',
                  }}
                  disabled={isLoading}
                />
              </div>
              {formErrors.fullName && (
                <p style={{ fontSize: '0.72rem', color: tokens.statusErrorText, margin: '4px 0 0 0' }}>{formErrors.fullName}</p>
              )}
            </div>

            {/* Username & Email Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px' }}>
              {/* Username */}
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: tokens.textPrimary, marginBottom: '6px' }}>
                  Username <span style={{ color: tokens.statusErrorText }}>*</span>
                </label>
                <div style={{ position: 'relative' }}>
                  <AtSign size={15} color="#94A3B8" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. rsharma"
                    style={{
                      width: '100%',
                      padding: '9px 12px 9px 36px',
                      borderRadius: '6px',
                      border: `1px solid ${formErrors.username ? tokens.statusErrorBorder : tokens.border}`,
                      fontSize: '0.82rem',
                      color: tokens.textPrimary,
                      outline: 'none',
                      boxSizing: 'border-box',
                      backgroundColor: formErrors.username ? 'rgba(239, 68, 68, 0.05)' : '#FFFFFF',
                    }}
                    disabled={isLoading}
                    autoComplete="off"
                  />
                </div>
                {formErrors.username && (
                  <p style={{ fontSize: '0.72rem', color: tokens.statusErrorText, margin: '4px 0 0 0' }}>{formErrors.username}</p>
                )}
              </div>

              {/* Email */}
              <div>
                <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: tokens.textPrimary, marginBottom: '6px' }}>
                  Corporate Email <span style={{ color: tokens.statusErrorText }}>*</span>
                </label>
                <div style={{ position: 'relative' }}>
                  <Mail size={15} color="#94A3B8" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="e.g. rsharma@acc-rmc.in"
                    style={{
                      width: '100%',
                      padding: '9px 12px 9px 36px',
                      borderRadius: '6px',
                      border: `1px solid ${formErrors.email ? tokens.statusErrorBorder : tokens.border}`,
                      fontSize: '0.82rem',
                      color: tokens.textPrimary,
                      outline: 'none',
                      boxSizing: 'border-box',
                      backgroundColor: formErrors.email ? 'rgba(239, 68, 68, 0.05)' : '#FFFFFF',
                    }}
                    disabled={isLoading}
                    autoComplete="off"
                  />
                </div>
                {formErrors.email && (
                  <p style={{ fontSize: '0.72rem', color: tokens.statusErrorText, margin: '4px 0 0 0' }}>{formErrors.email}</p>
                )}
              </div>
            </div>

            {/* Role Assignments */}
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 700, color: tokens.textPrimary, marginBottom: '8px' }}>
                Assign RBAC Roles <span style={{ color: tokens.statusErrorText }}>*</span>
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '8px' }}>
                {assignableRoles.map((role) => {
                  const isChecked = selectedRoles.includes(role);
                  return (
                    <button
                      type="button"
                      key={role}
                      onClick={() => handleRoleToggle(role)}
                      disabled={isLoading}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        border: isChecked ? `1px solid ${tokens.primaryAccentBorder}` : `1px solid ${tokens.borderLight}`,
                        backgroundColor: isChecked ? tokens.primaryAccentLight : '#FFFFFF',
                        color: isChecked ? tokens.primaryAccent : tokens.textSecondary,
                        cursor: 'pointer',
                        textAlign: 'left',
                        fontSize: '0.78rem',
                        fontWeight: isChecked ? 600 : 500,
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Shield size={14} color={isChecked ? tokens.primaryAccent : '#94A3B8'} />
                        <span>{role}</span>
                      </div>
                      <div
                        style={{
                          width: '16px',
                          height: '16px',
                          borderRadius: '4px',
                          border: isChecked ? `1px solid ${tokens.primaryAccent}` : `1px solid #CBD5E1`,
                          backgroundColor: isChecked ? tokens.primaryAccent : '#FFFFFF',
                          color: '#FFFFFF',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        {isChecked && <Check size={12} strokeWidth={3} />}
                      </div>
                    </button>
                  );
                })}
              </div>
              {formErrors.roles && (
                <p style={{ fontSize: '0.72rem', color: tokens.statusErrorText, margin: '6px 0 0 0' }}>{formErrors.roles}</p>
              )}
            </div>

            {/* Governance Hint */}
            <div
              style={{
                padding: '12px 14px',
                backgroundColor: tokens.surfaceSecondary,
                border: `1px solid ${tokens.borderLight}`,
                borderRadius: '8px',
                fontSize: '0.73rem',
                color: tokens.textSecondary,
                lineHeight: 1.5,
              }}
            >
              Upon account creation, the backend will generate a cryptographically random temporary password with a strict 72-hour expiration policy and force password rotation upon first login.
            </div>
          </div>

          {/* Footer Actions */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'flex-end',
              gap: '10px',
              padding: '12px 24px',
              borderTop: `1px solid ${tokens.border}`,
              backgroundColor: tokens.surfaceSecondary,
            }}
          >
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              style={secondaryButtonBase}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading}
              onClick={handleSubmit}
              style={{
                ...primaryButtonBase,
                padding: '8px 18px',
                fontSize: '0.82rem',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                backgroundColor: tokens.primaryAccent,
              }}
            >
              {isLoading ? 'Provisioning Account...' : 'Create Account'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
