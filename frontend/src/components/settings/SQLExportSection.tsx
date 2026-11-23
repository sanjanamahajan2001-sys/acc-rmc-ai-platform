import React, { useState } from 'react';
import { SqlExportResponseDTO, downloadSqlExport } from '../../services/settingsService';
import { DatabaseOverviewCards } from './DatabaseOverviewCards';
import { DatabaseOverviewDTO } from '../../services/settingsService';
import { Copy, Check, Download, FileCode, Shield, Loader2, Sparkles } from 'lucide-react';
import { enterpriseLightTokens as tokens } from '../manual-entry/enterpriseLightTokens';

interface SQLExportSectionProps {
  exportData: SqlExportResponseDTO | null;
  overview?: DatabaseOverviewDTO;
  loading: boolean;
}

export const SQLExportSection: React.FC<SQLExportSectionProps> = ({
  exportData,
  overview,
  loading,
}) => {
  const [copied, setCopied] = useState<boolean>(false);
  const [downloading, setDownloading] = useState<boolean>(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleCopy = async () => {
    if (!exportData?.sql_ddl) return;
    try {
      await navigator.clipboard.writeText(exportData.sql_ddl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error('Failed to copy SQL to clipboard:', err);
    }
  };

  const handleDownload = async () => {
    try {
      setDownloading(true);
      setDownloadError(null);
      await downloadSqlExport();
    } catch (err: any) {
      console.error('SQL export download failed:', err);
      setDownloadError('Failed to download SQL schema file.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
      {/* 1. Database Overview Cards */}
      <DatabaseOverviewCards overview={overview} loading={loading} />

      {/* 2. SQL DDL Header Banner & Action Bar */}
      <div
        style={{
          backgroundColor: tokens.surfacePrimary,
          border: `1px solid ${tokens.border}`,
          borderRadius: '10px',
          padding: '16px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          marginBottom: '16px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              backgroundColor: 'rgba(37, 99, 235, 0.08)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: tokens.primaryAccent,
            }}
          >
            <FileCode size={18} />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: '0.92rem', color: tokens.textPrimary }}>
              Read-Only PostgreSQL Schema DDL
            </div>
            <div style={{ fontSize: '0.76rem', color: tokens.textMuted }}>
              Clean generated SQL with table structures, keys, and foreign constraints. Zero credentials.
            </div>
          </div>
        </div>

        {/* Actions: Copy & Download */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {downloadError && (
            <span style={{ fontSize: '0.75rem', color: '#DC2626', fontWeight: 600 }}>
              {downloadError}
            </span>
          )}

          {/* Copy SQL Button */}
          <button
            type="button"
            onClick={handleCopy}
            disabled={loading || !exportData?.sql_ddl}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: '6px',
              backgroundColor: copied ? '#F0FDF4' : tokens.surfaceSecondary,
              color: copied ? '#059669' : tokens.textPrimary,
              border: copied ? '1px solid #86EFAC' : `1px solid ${tokens.border}`,
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: loading || !exportData?.sql_ddl ? 'not-allowed' : 'pointer',
              transition: 'all 0.15s ease',
            }}
            title="Copy entire SQL DDL to clipboard"
          >
            {copied ? <Check size={14} color="#059669" /> : <Copy size={14} />}
            <span>{copied ? 'Copied to Clipboard!' : 'Copy SQL'}</span>
          </button>

          {/* Download SQL Button */}
          <button
            type="button"
            onClick={handleDownload}
            disabled={loading || downloading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 16px',
              borderRadius: '6px',
              backgroundColor: '#3B82F6',
              color: '#FFFFFF',
              border: 'none',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: loading || downloading ? 'not-allowed' : 'pointer',
              boxShadow: '0 1px 2px rgba(59, 130, 246, 0.3)',
              transition: 'all 0.15s ease',
            }}
            title="Download authoritative PostgreSQL schema .sql file"
          >
            {downloading ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            <span>{downloading ? 'Downloading...' : 'Download .sql'}</span>
          </button>
        </div>
      </div>

      {/* 3. SQL Code Viewer Box */}
      <div
        style={{
          backgroundColor: '#0F172A',
          border: '1px solid #1E293B',
          borderRadius: '10px',
          overflow: 'hidden',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        }}
      >
        <div
          style={{
            padding: '8px 16px',
            backgroundColor: '#0B1120',
            borderBottom: '1px solid #1E293B',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.74rem',
            color: '#94A3B8',
            fontFamily: 'monospace',
          }}
        >
          <span>{exportData?.filename || 'acc_rmc_database_schema.sql'}</span>
          <span>{exportData?.tables_count || 0} Tables • PostgreSQL 17</span>
        </div>

        <pre
          style={{
            margin: 0,
            padding: '16px 20px',
            color: '#E2E8F0',
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
            fontSize: '0.8rem',
            lineHeight: 1.5,
            overflowX: 'auto',
            maxHeight: '600px',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
          }}
        >
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#94A3B8', padding: '20px 0' }}>
              <Loader2 size={16} className="animate-spin" />
              <span>Generating clean live schema DDL export...</span>
            </div>
          ) : (
            exportData?.sql_ddl || '-- No SQL DDL generated.'
          )}
        </pre>
      </div>
    </div>
  );
};
