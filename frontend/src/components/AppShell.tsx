import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { AppSidebar } from './AppSidebar';
import { AppNavbar } from './AppNavbar';
import { enterpriseLightTokens as tokens } from './manual-entry/enterpriseLightTokens';

interface AppShellProps {
  children: React.ReactNode;
}

export const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  // Close mobile drawer on route navigation
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  return (
    <div
      style={{
        display: 'flex',
        minHeight: '100vh',
        width: '100%',
        backgroundColor: tokens.pageBg,
        fontFamily: tokens.fontFamily,
        position: 'relative',
        overflowX: 'hidden',
      }}
    >
      {/* Sidebar (Desktop persistent + Mobile slide-over drawer) */}
      <AppSidebar
        mobileOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      {/* Main Content Column */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
          width: '100%',
        }}
      >
        {/* Top Navbar */}
        <AppNavbar
          onToggleMobileMenu={() => setMobileMenuOpen(!mobileMenuOpen)}
          mobileMenuOpen={mobileMenuOpen}
        />

        {/* Child Page Content */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', width: '100%', minWidth: 0 }}>
          {children}
        </div>
      </div>
    </div>
  );
};
