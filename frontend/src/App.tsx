import { SettingsPage } from './pages/SettingsPage';
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from './pages/LoginPage';
import { ChangePasswordPage } from './pages/ChangePasswordPage';
import { AdminUserManagementPage } from './pages/AdminUserManagementPage';
import { AuditGovernancePage } from './pages/AuditGovernancePage';
import { DatasetIngestionPage } from './pages/DatasetIngestionPage';
import { ManualProductionEntryPage } from './pages/ManualProductionEntryPage';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { AccessDenied } from './components/common/AccessDenied';
import { OperationsDashboardPage } from './pages/OperationsDashboardPage';

export const App: React.FC = () => {
  return (
    <Routes>
      {/* Public Authentication Routes */}
      <Route path="/acc/login" element={<LoginPage />} />
      <Route path="/login" element={<Navigate to="/acc/login" replace />} />

      {/* Forced Password Change Route */}
      <Route
        path="/acc/change-password"
        element={
          <ProtectedRoute requireForcedPasswordChange={true}>
            <ChangePasswordPage />
          </ProtectedRoute>
        }
      />

      {/* Administrative User Management Dashboard (Requires SUPER_ADMIN or ADMIN) */}
      <Route
        path="/acc/admin/users"
        element={
          <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'ADMIN']}>
            <AdminUserManagementPage />
          </ProtectedRoute>
        }
      />

      {/* Centralized Audit & Governance Center (Requires SUPER_ADMIN, ADMIN, or QUALITY_HEAD) */}
      <Route
        path="/acc/admin/audit"
        element={
          <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'ADMIN', 'QUALITY_HEAD']}>
            <AuditGovernancePage />
          </ProtectedRoute>
        }
      />

      {/* Settings: DB Preview & SQL Export (Requires SUPER_ADMIN, ADMIN, or QUALITY_HEAD) */}
      <Route
        path="/acc/admin/settings"
        element={
          <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'ADMIN', 'QUALITY_HEAD']}>
            <SettingsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/acc/settings"
        element={
          <ProtectedRoute allowedRoles={['SUPER_ADMIN', 'ADMIN', 'QUALITY_HEAD']}>
            <SettingsPage />
          </ProtectedRoute>
        }
      />

      {/* Dataset Ingestion */}
      <Route
        path="/acc/dataset-ingestion"
        element={
          <ProtectedRoute>
            <DatasetIngestionPage />
          </ProtectedRoute>
        }
      />

      {/* Manual Production Batch Entry */}
      <Route
        path="/acc/manual-production-entry"
        element={
          <ProtectedRoute>
            <ManualProductionEntryPage />
          </ProtectedRoute>
        }
      />

      {/* Quality Management System (Protected Core Application) */}
      <Route
        path="/acc"
        element={
          <ProtectedRoute>
            <OperationsDashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/acc/dashboard"
        element={
          <ProtectedRoute>
            <OperationsDashboardPage />
          </ProtectedRoute>
        }
      />

      {/* Global Access Denied Fallback */}
      <Route path="/access-denied" element={<AccessDenied />} />

      {/* Default Catch-all Redirect */}
      <Route path="*" element={<Navigate to="/acc" replace />} />
    </Routes>
  );
};

export default App;
