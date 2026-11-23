import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { X } from 'lucide-react';
import {
  ControlTowerIcon,
  CloudIngestIcon,
  BatchTicketIcon,
  PersonnelBadgeIcon,
  QualitySealIcon,
  PrecisionGearIcon,
} from './icons';
import { useAuth } from '../context/AuthContext';
import { enterpriseLightTokens as tokens } from './manual-entry/enterpriseLightTokens';

interface AppSidebarProps {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const AppSidebar: React.FC<AppSidebarProps> = ({ mobileOpen = false, onCloseMobile }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isSuperAdmin, isAdmin, isQualityHead } = useAuth();

  // Handle Escape key to close mobile drawer
  useEffect(() => {
    if (!mobileOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && onCloseMobile) {
        onCloseMobile();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mobileOpen, onCloseMobile]);

  const operationsItems = [
    { label: 'Operations Dashboard', path: '/acc/dashboard', icon: ControlTowerIcon },
  ];

  const ingestionItems = [
    { label: 'Dataset Ingestion', path: '/acc/dataset-ingestion', icon: CloudIngestIcon },
    { label: 'Manual Batch Entry', path: '/acc/manual-production-entry', icon: BatchTicketIcon },
  ];

  const adminItems = [
    ...((isAdmin || isSuperAdmin) ? [{ label: 'User Management', path: '/acc/admin/users', icon: PersonnelBadgeIcon }] : []),
    ...((isAdmin || isSuperAdmin || isQualityHead) ? [{ label: 'Audit & Governance', path: '/acc/admin/audit', icon: QualitySealIcon }] : []),
    ...((isAdmin || isSuperAdmin || isQualityHead) ? [{ label: 'Settings', path: '/acc/admin/settings', icon: PrecisionGearIcon }] : []),
  ];

  const isActive = (path: string) => {
    if (path === '/acc/dashboard' && (location.pathname === '/acc' || location.pathname === '/acc/' || location.pathname === '/acc/dashboard')) {
      return true;
    }
    return location.pathname === path;
  };

  const handleNavClick = (path: string) => {
    navigate(path);
    if (onCloseMobile) {
      onCloseMobile();
    }
  };

  const renderNavButton = (item: { label: string; path: string; icon: any }, idx: number) => {
    const Icon = item.icon;
    const active = isActive(item.path);
    return (
      <button
        key={idx}
        type="button"
        onClick={() => handleNavClick(item.path)}
        aria-label={`Navigate to ${item.label}`}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          width: '100%',
          minHeight: '44px',
          padding: '10px 14px',
          borderRadius: '6px',
          fontSize: '0.84rem',
          fontWeight: active ? 600 : 500,
          color: active ? tokens.primaryAccent : tokens.textSecondary,
          backgroundColor: active ? tokens.primaryAccentLight : 'transparent',
          border: active ? `1px solid ${tokens.primaryAccentBorder}` : '1px solid transparent',
          textAlign: 'left',
          cursor: 'pointer',
          transition: 'all 0.15s ease',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Icon size={18} />
          <span>{item.label}</span>
        </div>
        {active && (
          <span
            style={{
              fontSize: '0.68rem',
              fontWeight: 700,
              backgroundColor: tokens.primaryAccent,
              color: '#FFFFFF',
              padding: '2px 7px',
              borderRadius: '4px',
            }}
          >
            Active
          </span>
        )}
      </button>
    );
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {mobileOpen && (
        <div
          className="sidebar-mobile-backdrop"
          onClick={onCloseMobile}
          aria-hidden="true"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.5)',
            zIndex: 90,
            backdropFilter: 'blur(2px)',
          }}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`app-sidebar-container ${mobileOpen ? 'mobile-open' : ''}`}
        aria-label="Platform Sidebar Navigation"
        style={{
          backgroundColor: '#FFFFFF',
          borderRight: `1px solid ${tokens.border}`,
          display: 'flex',
          flexDirection: 'column',
          height: '100vh',
          fontFamily: tokens.fontFamily,
          boxSizing: 'border-box',
        }}
      >
        {/* Brand Section */}
        <div
          style={{
            padding: '16px 18px',
            borderBottom: `1px solid ${tokens.borderLight}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '10px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '1.3rem' }}>🏗️</span>
            <div>
              <div style={{ fontWeight: 800, fontSize: '0.88rem', color: tokens.textPrimary, letterSpacing: '-0.02em' }}>
                ACC RMC AI PLATFORM
              </div>
              <div style={{ fontSize: '0.7rem', color: tokens.textMuted }}>
                Cement Strength & Quality
              </div>
            </div>
          </div>

          {/* Close button on mobile */}
          {onCloseMobile && (
            <button
              type="button"
              className="sidebar-close-btn-mobile"
              onClick={onCloseMobile}
              aria-label="Close navigation sidebar"
              style={{
                background: 'transparent',
                border: `1px solid ${tokens.border}`,
                borderRadius: '6px',
                minWidth: '36px',
                minHeight: '36px',
                display: 'none', // Shown on mobile via CSS
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                color: tokens.textSecondary,
                padding: 0,
              }}
            >
              <X size={18} />
            </button>
          )}
        </div>

        {/* Main Nav Section */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '14px 10px' }}>
          {/* Operations Section */}
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: tokens.textMuted, textTransform: 'uppercase', padding: '6px 12px', letterSpacing: '0.05em' }}>
            Operations
          </div>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginBottom: '14px' }}>
            {operationsItems.map(renderNavButton)}
          </nav>

          {/* Data Ingestion Section */}
          <div style={{ fontSize: '0.68rem', fontWeight: 700, color: tokens.textMuted, textTransform: 'uppercase', padding: '6px 12px', letterSpacing: '0.05em', borderTop: `1px solid ${tokens.borderLight}`, paddingTop: '12px' }}>
            Data Ingestion
          </div>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px', marginBottom: '14px' }}>
            {ingestionItems.map(renderNavButton)}
          </nav>

          {/* Administration Section */}
          {(isAdmin || isSuperAdmin || isQualityHead) && (
            <>
              <div style={{ fontSize: '0.68rem', fontWeight: 700, color: tokens.textMuted, textTransform: 'uppercase', padding: '6px 12px', letterSpacing: '0.05em', borderTop: `1px solid ${tokens.borderLight}`, paddingTop: '12px' }}>
                Administration
              </div>
              <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
                {adminItems.map(renderNavButton)}
              </nav>
            </>
          )}
        </div>

        {/* Footer info */}
        <div style={{ padding: '12px 16px', borderTop: `1px solid ${tokens.borderLight}`, fontSize: '0.72rem', color: tokens.textMuted }}>
          ACC RMC Enterprise v2.4
        </div>
      </aside>
    </>
  );
};
