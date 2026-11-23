import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { AuditGovernancePage } from '../pages/AuditGovernancePage';
import { auditService } from '../services/auditService';
import { AuthProvider } from '../context/AuthContext';
import { ProtectedRoute } from '../components/common/ProtectedRoute';
import { AccessDenied } from '../components/common/AccessDenied';
import { apiClient, setAuthToken, clearAuthToken } from '../services/apiClient';
import { UserIdentity } from '../types/auth';

// Mock audit service
vi.mock('../services/auditService', () => ({
  auditService: {
    getEvents: vi.fn(),
    getEventById: vi.fn(),
    getMetrics: vi.fn(),
    getCorrelationTrace: vi.fn(),
    getExportUrl: vi.fn().mockReturnValue('/api/v1/audit/export?format=csv'),
  },
}));

const mockAuditEvents = {
  items: [
    {
      id: 'audit-001',
      timestamp: '2026-09-16T10:00:00Z',
      module: 'AUTH',
      event_type: 'LOGIN_SUCCESS',
      action: 'LOGIN',
      severity: 'INFO',
      result: 'SUCCESS',
      actor: {
        user_id: 'usr-admin-01',
        username: 'admin',
        roles: ['SUPER_ADMIN', 'ADMIN'],
        ip_address: '192.168.1.1',
      },
      target: {
        entity_type: 'User',
        entity_id: 'admin',
      },
      correlation_id: 'TRACE-TEST-001',
      details: { client: 'web' },
    },
    {
      id: 'audit-002',
      timestamp: '2026-09-16T10:05:00Z',
      module: 'DATA_INGESTION',
      event_type: 'INGESTION_PERSISTENCE_COMPLETED',
      action: 'IMPORT',
      severity: 'INFO',
      result: 'SUCCESS',
      actor: {
        user_id: 'usr-admin-01',
        username: 'admin',
        roles: ['ADMIN'],
        ip_address: '192.168.1.1',
      },
      target: {
        entity_type: 'Dataset',
        entity_id: 'DS-001',
      },
      correlation_id: 'TRACE-TEST-002',
      details: { persisted_rows: 50 },
    },
  ],
  total: 2,
  page: 1,
  page_size: 25,
  total_pages: 1,
};

const mockAuditMetrics = {
  total_events: 2,
  successful_events: 2,
  failed_events: 0,
  denied_events: 0,
  events_last_24h: 2,
  module_breakdown: {
    AUTH: 1,
    DATA_INGESTION: 1,
  },
};

describe('Phase 12: Audit & Governance Center Frontend Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearAuthToken();
    (auditService.getEvents as any).mockResolvedValue(mockAuditEvents);
    (auditService.getMetrics as any).mockResolvedValue(mockAuditMetrics);
  });

  const renderAuditWithUser = (mockUser: UserIdentity | null, initialPath = '/acc/admin/audit') => {
    if (mockUser) {
      setAuthToken('valid-test-token');
      vi.spyOn(apiClient, 'get').mockImplementation(async (path: string) => {
        if (path === '/auth/me') return mockUser;
        return null;
      });
    }

    return render(
      <MemoryRouter initialEntries={[initialPath]}>
        <AuthProvider>
          <Routes>
            <Route
              path="/acc/admin/audit"
              element={
                <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'ADMIN', 'QUALITY_HEAD']}>
                  <AuditGovernancePage />
                </ProtectedRoute>
              }
            />
            <Route path="/access-denied" element={<AccessDenied />} />
            <Route path="/acc/login" element={<div>Mock Login Page</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );
  };

  it('allows access for SUPER_ADMIN role', async () => {
    const superAdminUser: UserIdentity = {
      id: 'super-1',
      username: 'superadmin',
      email: 'super@acc-rmc.in',
      full_name: 'Super Admin User',
      roles: ['SUPER_ADMIN'],
      account_status: 'ACTIVE',
      password_status: 'NORMAL',
      must_change_password: false,
    };

    renderAuditWithUser(superAdminUser);

    await waitFor(() => {
      expect(screen.getByText(/Audit & Governance Center/i)).toBeInTheDocument();
      expect(screen.getByText('LOGIN_SUCCESS')).toBeInTheDocument();
      expect(screen.getByText('INGESTION_PERSISTENCE_COMPLETED')).toBeInTheDocument();
    });
  });

  it('allows access for QUALITY_HEAD role', async () => {
    const qualityHeadUser: UserIdentity = {
      id: 'qh-1',
      username: 'quality_head',
      email: 'qh@acc-rmc.in',
      full_name: 'Quality Head User',
      roles: ['QUALITY_HEAD'],
      account_status: 'ACTIVE',
      password_status: 'NORMAL',
      must_change_password: false,
    };

    renderAuditWithUser(qualityHeadUser);

    await waitFor(() => {
      expect(screen.getByText(/Audit & Governance Center/i)).toBeInTheDocument();
    });
  });

  it('denies access and redirects to access-denied for PLANT_OPERATOR role', async () => {
    const operatorUser: UserIdentity = {
      id: 'op-1',
      username: 'operator',
      email: 'op@acc-rmc.in',
      full_name: 'Plant Operator User',
      roles: ['PLANT_OPERATOR'],
      account_status: 'ACTIVE',
      password_status: 'NORMAL',
      must_change_password: false,
    };

    renderAuditWithUser(operatorUser);

    await waitFor(() => {
      expect(screen.queryByText(/Audit & Governance Center/i)).not.toBeInTheDocument();
      expect(screen.getByText(/Access Restricted/i)).toBeInTheDocument();
    });
  });

  it('displays metrics cards accurately from live backend data', async () => {
    const adminUser: UserIdentity = {
      id: 'admin-1',
      username: 'admin',
      email: 'admin@acc-rmc.in',
      full_name: 'Admin User',
      roles: ['ADMIN'],
      account_status: 'ACTIVE',
      password_status: 'NORMAL',
      must_change_password: false,
    };

    renderAuditWithUser(adminUser);

    await waitFor(() => {
      expect(screen.getByText('Total Audit Events')).toBeInTheDocument();
      expect(screen.getByText('Successful Actions')).toBeInTheDocument();
      expect(screen.getByText('Failed Operations')).toBeInTheDocument();
      expect(screen.getByText('Security Denials')).toBeInTheDocument();
    });
  });

  it('opens detail inspector drawer when event row is clicked', async () => {
    const adminUser: UserIdentity = {
      id: 'admin-1',
      username: 'admin',
      email: 'admin@acc-rmc.in',
      full_name: 'Admin User',
      roles: ['ADMIN'],
      account_status: 'ACTIVE',
      password_status: 'NORMAL',
      must_change_password: false,
    };

    renderAuditWithUser(adminUser);

    await waitFor(() => {
      expect(screen.getByText('LOGIN_SUCCESS')).toBeInTheDocument();
    });

    const eventRow = screen.getByText('LOGIN_SUCCESS');
    fireEvent.click(eventRow);

    await waitFor(() => {
      expect(screen.getByText('Audit Event Inspector')).toBeInTheDocument();
      expect(screen.getByText('Actor (Who)')).toBeInTheDocument();
      expect(screen.getByText('Target Object (What)')).toBeInTheDocument();
    });
  });
});
