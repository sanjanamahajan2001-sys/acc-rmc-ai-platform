import React, { useState, useEffect, useCallback } from 'react';
import { AppShell } from '../components/AppShell';
import { DatabasePreviewResponseDTO, SqlExportResponseDTO, fetchDatabasePreview, fetchSqlExport } from '../services/settingsService';
import { DBPreviewSection } from '../components/settings/DBPreviewSection';
import { SQLExportSection } from '../components/settings/SQLExportSection';
import { EngineeringCalibreSection } from '../components/settings/EngineeringCalibreSection';
import { Database, Code2, RefreshCw, AlertCircle, Layers, Sliders } from 'lucide-react';
import { enterpriseLightTokens as tokens } from '../components/manual-entry/enterpriseLightTokens';
import { useTour } from '../context/TourContext';

export const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'CALIBRE' | 'PREVIEW' | 'SQL_EXPORT'>('CALIBRE');
  const [previewData, setPreviewData] = useState<DatabasePreviewResponseDTO | null>(null);
  const [exportData, setExportData] = useState<SqlExportResponseDTO | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const { currentStep } = useTour();

  useEffect(() => {
    if (!currentStep) return;
    if (currentStep.id.startsWith('settings-calibre')) {
      setActiveTab('CALIBRE');
    } else if (currentStep.id.startsWith('settings-schema')) {
      setActiveTab('PREVIEW');
    } else if (currentStep.id.startsWith('settings-sql')) {
      setActiveTab('SQL_EXPORT');
    }
  }, [currentStep?.id]);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [prevRes, expRes] = await Promise.all([
        fetchDatabasePreview(),
        fetchSqlExport(),
      ]);
      setPreviewData(prevRes);
      setExportData(expRes);
    } catch (err: any) {
      console.error('Failed to load database settings metadata:', err);
      setError(err?.response?.data?.detail || 'Failed to inspect live database schema.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const tabs = [
    { key: 'CALIBRE', label: 'Engineering & Calculation Calibre', icon: Sliders },
    { key: 'PREVIEW', label: 'Schema Viewer', icon: Layers },
    { key: 'SQL_EXPORT', label: 'SQL DDL Export', icon: Code2 },
  ];

  return (
    <AppShell>
      <main
        className="page-main-container"
        style={{
          minWidth: 0,
          width: '100%',
          boxSizing: 'border-box',
          overflowX: 'hidden',
        }}
      >
        {/* Breadcrumb */}
        <div style={{ fontSize: '0.75rem', color: tokens.textMuted, marginBottom: '8px' }}>
          ACC Platform / Administration / <span style={{ color: tokens.primaryAccent, fontWeight: 600 }}>Settings</span>
        </div>

        {/* Header Banner with Title & Tab Switcher */}
        <div className="settings-header-banner">
          {/* Title & Badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0, flex: '1 1 300px' }}>
            <div
              style={{
                width: '40px',
                height: '40px',
                minWidth: '40px',
                borderRadius: '8px',
                backgroundColor: 'rgba(37, 99, 235, 0.08)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: tokens.primaryAccent,
              }}
            >
              {activeTab === 'CALIBRE' ? <Sliders size={20} /> : <Database size={20} />}
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <h1 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0, color: tokens.textPrimary, letterSpacing: '-0.01em' }}>
                  {activeTab === 'CALIBRE'
                    ? 'Engineering & Calculation Calibre Governance'
                    : 'PostgreSQL Schema Viewer & Live Introspection'}
                </h1>
                <span
                  style={{
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    backgroundColor: 'rgba(5, 150, 105, 0.08)',
                    color: '#059669',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    border: '1px solid rgba(5, 150, 105, 0.2)',
                    whiteSpace: 'nowrap',
                  }}
                >
                  LIVE CONFIG
                </span>
              </div>
              <p style={{ fontSize: '0.78rem', color: tokens.textMuted, margin: '2px 0 0 0' }}>
                {activeTab === 'CALIBRE'
                  ? 'Inspect, calibrate, and persist IS 456 / IS 10262 standards, statistical Z-factors, and solver constraints.'
                  : 'Zero mock metadata. 100% authoritative read-only inspection of active database tables and relationships.'}
              </p>
            </div>
          </div>

          {/* Subsection Tabs Switcher */}
          <div data-tour="settings-nav-tabs" className="settings-tabs-container">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const active = activeTab === tab.key;
              return (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => setActiveTab(tab.key as any)}
                  aria-label={`Switch to ${tab.label}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '6px 14px',
                    borderRadius: '6px',
                    fontSize: '0.78rem',
                    fontWeight: active ? 700 : 500,
                    color: active ? tokens.primaryAccent : tokens.textSecondary,
                    backgroundColor: active ? '#FFFFFF' : 'transparent',
                    border: 'none',
                    boxShadow: active ? '0 1px 3px rgba(0,0,0,0.06)' : 'none',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    whiteSpace: 'nowrap',
                  }}
                >
                  <Icon size={14} color={active ? tokens.primaryAccent : '#64748B'} style={{ flexShrink: 0 }} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Error Notification */}
        {error && (
          <div
            style={{
              padding: '12px 16px',
              backgroundColor: '#FEE2E2',
              border: '1px solid #FCA5A5',
              borderRadius: '8px',
              color: '#991B1B',
              fontSize: '0.82rem',
              marginBottom: '16px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Active Subsection Render */}
        <div style={{ width: '100%', minWidth: 0 }}>
          {activeTab === 'CALIBRE' ? (
            <EngineeringCalibreSection />
          ) : activeTab === 'PREVIEW' ? (
            <div data-tour="settings-schema-viewer">
              <DBPreviewSection
                data={previewData}
                loading={loading}
                onRefresh={loadData}
              />
            </div>
          ) : (
            <div data-tour="settings-sql-export">
              <SQLExportSection
                exportData={exportData}
                overview={previewData?.overview}
                loading={loading}
              />
            </div>
          )}
        </div>
      </main>
    </AppShell>
  );
};

export default SettingsPage;
