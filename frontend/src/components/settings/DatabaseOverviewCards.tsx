import React from 'react';
import { DatabaseOverviewDTO } from '../../services/settingsService';
import { Table, Columns, Link2, Database, Clock } from 'lucide-react';
import { enterpriseLightTokens as tokens } from '../manual-entry/enterpriseLightTokens';

interface DatabaseOverviewCardsProps {
  overview?: DatabaseOverviewDTO;
  loading?: boolean;
}

export const DatabaseOverviewCards: React.FC<DatabaseOverviewCardsProps> = ({
  overview,
  loading = false,
}) => {
  const cardStyle: React.CSSProperties = {
    backgroundColor: tokens.surfacePrimary,
    borderRadius: '10px',
    border: `1px solid ${tokens.border}`,
    padding: '16px 20px',
    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'space-between',
    minWidth: 0,
  };

  if (loading || !overview) {
    return (
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '14px',
          marginBottom: '20px',
        }}
      >
        {[1, 2, 3, 4].map((i) => (
          <div key={i} style={{ ...cardStyle, minHeight: '100px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
              <div style={{ height: '12px', width: '90px', backgroundColor: '#E2E8F0', borderRadius: '4px' }} />
              <div style={{ height: '20px', width: '20px', backgroundColor: '#E2E8F0', borderRadius: '4px' }} />
            </div>
            <div style={{ height: '24px', width: '60px', backgroundColor: '#E2E8F0', borderRadius: '4px', marginBottom: '6px' }} />
            <div style={{ height: '10px', width: '120px', backgroundColor: '#F1F5F9', borderRadius: '4px' }} />
          </div>
        ))}
      </div>
    );
  }

  const timeFormatted = overview.retrieved_at_utc
    ? new Date(overview.retrieved_at_utc).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '';

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '14px',
        marginBottom: '20px',
      }}
    >
      {/* 1. Public Tables */}
      <div style={cardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: tokens.textSecondary, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Public Tables
          </span>
          <div style={{ padding: '5px', backgroundColor: 'rgba(37, 99, 235, 0.08)', borderRadius: '6px', color: tokens.primaryAccent }}>
            <Table size={16} />
          </div>
        </div>
        <div style={{ fontSize: '1.65rem', fontWeight: 800, color: tokens.textPrimary, lineHeight: 1.1, marginBottom: '4px' }}>
          {overview.public_tables_count}
        </div>
        <div style={{ fontSize: '0.72rem', color: tokens.textMuted }}>
          PostgreSQL Base Tables
        </div>
      </div>

      {/* 2. Total Columns */}
      <div style={cardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: tokens.textSecondary, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Total Columns
          </span>
          <div style={{ padding: '5px', backgroundColor: 'rgba(13, 148, 136, 0.08)', borderRadius: '6px', color: '#0D9488' }}>
            <Columns size={16} />
          </div>
        </div>
        <div style={{ fontSize: '1.65rem', fontWeight: 800, color: tokens.textPrimary, lineHeight: 1.1, marginBottom: '4px' }}>
          {overview.total_columns_count}
        </div>
        <div style={{ fontSize: '0.72rem', color: tokens.textMuted }}>
          Across all schemas
        </div>
      </div>

      {/* 3. FK Relations */}
      <div style={cardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: tokens.textSecondary, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            FK Relations
          </span>
          <div style={{ padding: '5px', backgroundColor: 'rgba(124, 58, 237, 0.08)', borderRadius: '6px', color: '#7C3AED' }}>
            <Link2 size={16} />
          </div>
        </div>
        <div style={{ fontSize: '1.65rem', fontWeight: 800, color: tokens.textPrimary, lineHeight: 1.1, marginBottom: '4px' }}>
          {overview.foreign_keys_count}
        </div>
        <div style={{ fontSize: '0.72rem', color: tokens.textMuted }}>
          Referential Constraints
        </div>
      </div>

      {/* 4. Database Name */}
      <div style={cardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
          <span style={{ fontSize: '0.72rem', fontWeight: 700, color: tokens.textSecondary, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Database
          </span>
          <div style={{ padding: '5px', backgroundColor: 'rgba(5, 150, 105, 0.08)', borderRadius: '6px', color: '#059669' }}>
            <Database size={16} />
          </div>
        </div>
        <div
          style={{
            fontSize: '1.25rem',
            fontWeight: 800,
            color: tokens.textPrimary,
            lineHeight: 1.2,
            marginBottom: '4px',
            wordBreak: 'break-all',
          }}
          title={overview.database_name}
        >
          {overview.database_name}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.72rem', color: tokens.textMuted }}>
          <Clock size={12} />
          <span>{timeFormatted}</span>
        </div>
      </div>
    </div>
  );
};
