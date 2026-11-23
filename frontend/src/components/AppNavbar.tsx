import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTour } from '../context/TourContext';
import { enterpriseLightTokens as tokens, primaryButtonBase, secondaryButtonBase } from './manual-entry/enterpriseLightTokens';
import { LogOut, Database, Layers, User as UserIcon, Menu, X, HelpCircle } from 'lucide-react';
import { AccountAdminModal } from './admin/AccountAdminModal';

interface AppNavbarProps {
  onToggleMobileMenu?: () => void;
  mobileMenuOpen?: boolean;
}

export const AppNavbar: React.FC<AppNavbarProps> = ({ onToggleMobileMenu, mobileMenuOpen }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { resetTourStatus } = useTour();
  const [showAccountModal, setShowAccountModal] = useState(false);

  return (
    <>
      <header
        className="app-header-container"
        style={{
          height: '56px',
          minHeight: '56px',
          backgroundColor: '#FFFFFF',
          borderBottom: `1px solid ${tokens.border}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'sticky',
          top: 0,
          zIndex: 30,
          fontFamily: tokens.fontFamily,
          boxSizing: 'border-box',
          width: '100%',
        }}
      >
        {/* Left Section: Mobile Menu Toggle + Platform Branding */}
        <div
          className="navbar-brand-section"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            minWidth: 0,
            flex: '1 1 auto',
          }}
        >
          {/* Hamburger toggle button (visible on mobile/tablet <= 768px via CSS) */}
          {onToggleMobileMenu && (
            <button
              type="button"
              className="mobile-nav-toggle-btn"
              onClick={onToggleMobileMenu}
              aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
              aria-expanded={mobileMenuOpen}
              style={{
                background: 'transparent',
                border: `1px solid ${tokens.border}`,
                borderRadius: '6px',
                width: '36px',
                height: '36px',
                minWidth: '36px',
                minHeight: '36px',
                display: 'none', // Handled via CSS media query
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                color: tokens.textPrimary,
                padding: 0,
                flexShrink: 0,
                boxSizing: 'border-box',
              }}
            >
              {mobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
          )}

          <div
            className="navbar-brand-link" data-tour="navbar-brand"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              cursor: 'pointer',
              minWidth: 0,
              flexShrink: 1,
            }}
            onClick={() => navigate('/acc/dashboard')}
            title="ACC RMC Dashboard"
          >
            <span
              className="navbar-brand-title"
              style={{
                fontWeight: 800,
                fontSize: '0.92rem',
                color: tokens.textPrimary,
                whiteSpace: 'nowrap',
                letterSpacing: '-0.01em',
              }}
            >
              ACC RMC Platform
            </span>
            <span
              className="navbar-subtitle-text"
              style={{
                fontSize: '0.75rem',
                color: tokens.textMuted,
                whiteSpace: 'nowrap',
              }}
            >
              | Ready Mix Concrete
            </span>
          </div>
        </div>

        {/* Right Action Items: User Profile & Role, Ingestion Shortcuts, Logout */}
        <div
          className="navbar-actions-section"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            flexShrink: 0,
          }}
        >
          {/* Box 1: Manual Production Entry (Desktop only) */}
          <button
            type="button"
            className="navbar-desktop-action-btn"
            data-tour="navbar-manual-entry"
            onClick={() => navigate('/acc/manual-production-entry')}
            aria-label="Navigate to Manual Production Entry"
            style={{
              ...secondaryButtonBase,
              height: '36px',
              minHeight: '36px',
              padding: '0 12px',
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              borderRadius: '6px',
              boxSizing: 'border-box',
            }}
          >
            <Layers size={14} color={tokens.textSecondary} />
            <span>Manual Entry</span>
          </button>

          {/* Box 2: Dataset Ingestion (Desktop only) */}
          <button
            type="button"
            className="navbar-desktop-action-btn"
            data-tour="navbar-ingestion"
            onClick={() => navigate('/acc/dataset-ingestion')}
            aria-label="Navigate to Dataset Ingestion"
            style={{
              ...primaryButtonBase,
              height: '36px',
              minHeight: '36px',
              padding: '0 14px',
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              borderRadius: '6px',
              backgroundColor: tokens.primaryAccent,
              boxSizing: 'border-box',
            }}
          >
            <Database size={14} color="#FFFFFF" />
            <span>Ingestion</span>
          </button>

                    {/* Quick Tour / Help Button */}
          <button
            type="button"
            className="navbar-quick-tour-btn"
            data-tour="navbar-quick-tour"
            onClick={resetTourStatus}
            aria-label="Start Platform Guided Tour"
            title="Start Interactive Guided Tour"
            style={{
              backgroundColor: tokens.surfaceSecondary,
              border: `1px solid ${tokens.border}`,
              borderRadius: '6px',
              height: '36px',
              minHeight: '36px',
              padding: '0 10px',
              fontSize: '0.8rem',
              color: tokens.textPrimary,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              cursor: 'pointer',
              fontWeight: 600,
              flexShrink: 0,
              boxSizing: 'border-box',
            }}
          >
            <HelpCircle size={15} color={tokens.primaryAccent} />
            <span className="navbar-quick-tour-text" style={{ fontSize: '0.78rem' }}>Quick Tour</span>
          </button>

          {/* User profile & role pill button */}
          <button
            type="button"
            className="navbar-user-profile-btn"
            aria-label="User Profile and Account Settings"
            onClick={() => setShowAccountModal(true)}
            title="Click to view profile & change password"
            style={{
              height: '36px',
              minHeight: '36px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '0 10px',
              backgroundColor: tokens.surfaceSecondary,
              border: `1px solid ${tokens.border}`,
              borderRadius: '6px',
              fontSize: '0.8rem',
              color: tokens.textPrimary,
              cursor: 'pointer',
              outline: 'none',
              transition: 'all 0.15s ease-in-out',
              boxSizing: 'border-box',
              flexShrink: 0,
            }}
          >
            <UserIcon size={14} color={tokens.primaryAccent} style={{ flexShrink: 0 }} />
            <span
              className="navbar-username-label"
              style={{
                fontWeight: 600,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                maxWidth: '90px',
                fontSize: '0.78rem',
              }}
            >
              {user?.full_name || user?.username || 'admin'}
            </span>
            <span
              className="navbar-role-badge"
              style={{
                fontSize: '0.62rem',
                fontWeight: 700,
                padding: '2px 5px',
                backgroundColor: tokens.primaryAccentLight,
                color: tokens.primaryAccent,
                borderRadius: '4px',
                flexShrink: 0,
                whiteSpace: 'nowrap',
                letterSpacing: '0.02em',
              }}
            >
              {user?.roles?.[0] === 'SUPER_ADMIN' ? 'SUPER' : user?.roles?.[0] || 'ADMIN'}
            </span>
          </button>

          {/* Logout button */}
          <button
            type="button"
            onClick={logout}
            aria-label="Sign out of platform"
            title="Sign out"
            className="navbar-logout-btn"
            style={{
              backgroundColor: 'transparent',
              border: `1px solid ${tokens.border}`,
              borderRadius: '6px',
              height: '36px',
              minHeight: '36px',
              minWidth: '36px',
              padding: '0 10px',
              fontSize: '0.8rem',
              color: tokens.textSecondary,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              cursor: 'pointer',
              flexShrink: 0,
              boxSizing: 'border-box',
            }}
          >
            <LogOut size={14} />
            <span className="navbar-logout-text">Logout</span>
          </button>
        </div>
      </header>

      {/* Account Details & Change Password Modal */}
      <AccountAdminModal
        isOpen={showAccountModal}
        onClose={() => setShowAccountModal(false)}
      />
    </>
  );
};
