import React, { useState, useMemo } from 'react';
import { DatabasePreviewResponseDTO, TableMetadataDTO } from '../../services/settingsService';
import { DatabaseOverviewCards } from './DatabaseOverviewCards';
import { TableSchemaCard } from './TableSchemaCard';
import { Search, ZoomIn, ZoomOut, RotateCcw, RefreshCw, AlertCircle, Layers } from 'lucide-react';
import { enterpriseLightTokens as tokens } from '../manual-entry/enterpriseLightTokens';

interface DBPreviewSectionProps {
  data: DatabasePreviewResponseDTO | null;
  loading: boolean;
  onRefresh: () => void;
}

export const DBPreviewSection: React.FC<DBPreviewSectionProps> = ({
  data,
  loading,
  onRefresh,
}) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [zoomLevel, setZoomLevel] = useState<number>(100);

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 10, 140));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev - 10, 70));
  const handleZoomReset = () => setZoomLevel(100);

  // Filter tables by search query (matching table name or column name)
  const filteredTables = useMemo(() => {
    if (!data?.tables) return [];
    if (!searchTerm.trim()) return data.tables;

    const term = searchTerm.toLowerCase().trim();
    return data.tables.filter((tbl: TableMetadataDTO) => {
      if (tbl.name.toLowerCase().includes(term)) return true;
      return tbl.columns.some((c) => c.name.toLowerCase().includes(term));
    });
  }, [data?.tables, searchTerm]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
      {/* 1. Database Overview Cards */}
      <DatabaseOverviewCards overview={data?.overview} loading={loading} />

      {/* 2. Search & Toolbar Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
          marginBottom: '18px',
          backgroundColor: tokens.surfacePrimary,
          border: `1px solid ${tokens.border}`,
          borderRadius: '8px',
          padding: '10px 14px',
          boxShadow: '0 1px 2px rgba(0, 0, 0, 0.03)',
        }}
      >
        {/* Search Input */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: '#F8FAFC',
            border: `1px solid ${tokens.border}`,
            borderRadius: '6px',
            padding: '6px 12px',
            flex: '1 1 280px',
            maxWidth: '450px',
          }}
        >
          <Search size={15} color={tokens.textMuted} />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search tables or columns (e.g. 'audit', 'user_id')..."
            style={{
              border: 'none',
              backgroundColor: 'transparent',
              outline: 'none',
              fontSize: '0.82rem',
              color: tokens.textPrimary,
              width: '100%',
            }}
          />
          {searchTerm && (
            <button
              type="button"
              onClick={() => setSearchTerm('')}
              style={{
                background: 'transparent',
                border: 'none',
                color: tokens.textMuted,
                cursor: 'pointer',
                fontSize: '0.75rem',
                padding: '0 2px',
              }}
            >
              ✕
            </button>
          )}
        </div>

        {/* Action Controls: Zoom & Refresh */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Zoom controls */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              backgroundColor: '#F8FAFC',
              border: `1px solid ${tokens.border}`,
              borderRadius: '6px',
              overflow: 'hidden',
            }}
          >
            <button
              type="button"
              onClick={handleZoomOut}
              disabled={zoomLevel <= 70}
              style={{
                background: 'transparent',
                border: 'none',
                padding: '6px 8px',
                cursor: zoomLevel <= 70 ? 'not-allowed' : 'pointer',
                color: tokens.textSecondary,
                display: 'flex',
                alignItems: 'center',
              }}
              title="Zoom Out"
            >
              <ZoomOut size={14} />
            </button>
            <span
              onClick={handleZoomReset}
              style={{
                fontSize: '0.74rem',
                fontWeight: 600,
                color: tokens.textPrimary,
                padding: '0 6px',
                cursor: 'pointer',
                userSelect: 'none',
              }}
              title="Reset Zoom"
            >
              {zoomLevel}%
            </span>
            <button
              type="button"
              onClick={handleZoomIn}
              disabled={zoomLevel >= 140}
              style={{
                background: 'transparent',
                border: 'none',
                padding: '6px 8px',
                cursor: zoomLevel >= 140 ? 'not-allowed' : 'pointer',
                color: tokens.textSecondary,
                display: 'flex',
                alignItems: 'center',
              }}
              title="Zoom In"
            >
              <ZoomIn size={14} />
            </button>
          </div>

          {/* Reset Zoom Button */}
          <button
            type="button"
            onClick={handleZoomReset}
            style={{
              background: '#F8FAFC',
              border: `1px solid ${tokens.border}`,
              borderRadius: '6px',
              padding: '6px 10px',
              cursor: 'pointer',
              color: tokens.textSecondary,
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.76rem',
              fontWeight: 600,
            }}
            title="Reset Zoom to 100%"
          >
            <RotateCcw size={13} />
          </button>

          {/* Refresh Schema Button */}
          <button
            type="button"
            onClick={onRefresh}
            disabled={loading}
            style={{
              background: '#F8FAFC',
              border: `1px solid ${tokens.border}`,
              borderRadius: '6px',
              padding: '6px 12px',
              cursor: loading ? 'not-allowed' : 'pointer',
              color: tokens.textPrimary,
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '0.78rem',
              fontWeight: 600,
            }}
            title="Refresh Live Database Schema"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* 3. Tables Count Indicator */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', fontSize: '0.78rem', color: tokens.textMuted }}>
        <div>
          Showing <strong>{filteredTables.length}</strong> of <strong>{data?.tables.length || 0}</strong> base tables
          {searchTerm && <span> (filtered by &quot;{searchTerm}&quot;)</span>}
        </div>
      </div>

      {/* 4. Responsive Tables Grid */}
      {filteredTables.length === 0 ? (
        <div
          style={{
            backgroundColor: tokens.surfacePrimary,
            border: `1px solid ${tokens.border}`,
            borderRadius: '10px',
            padding: '40px 20px',
            textAlign: 'center',
            color: tokens.textMuted,
          }}
        >
          <AlertCircle size={28} style={{ margin: '0 auto 8px auto', opacity: 0.5 }} />
          <div style={{ fontWeight: 600, fontSize: '0.9rem', color: tokens.textSecondary }}>No matching tables found</div>
          <div style={{ fontSize: '0.78rem', marginTop: '4px' }}>Try clearing the search query or refreshing the schema inspection.</div>
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: `repeat(auto-fill, minmax(${Math.round(300 * (zoomLevel / 100))}px, 1fr))`,
            gap: '16px',
            transformOrigin: 'top left',
          }}
        >
          {filteredTables.map((tbl: TableMetadataDTO) => (
            <TableSchemaCard key={tbl.name} table={tbl} />
          ))}
        </div>
      )}
    </div>
  );
};
