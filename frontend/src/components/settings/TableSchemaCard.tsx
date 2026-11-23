import React, { useState } from 'react';
import { TableMetadataDTO, ColumnMetadataDTO, ForeignKeyDetailDTO } from '../../services/settingsService';
import { Table, Key, Link2, ArrowDown, ChevronRight } from 'lucide-react';
import { enterpriseLightTokens as tokens } from '../manual-entry/enterpriseLightTokens';

interface TableSchemaCardProps {
  table: TableMetadataDTO;
}

export const TableSchemaCard: React.FC<TableSchemaCardProps> = ({ table }) => {
  const [activeFkHover, setActiveFkHover] = useState<ForeignKeyDetailDTO | null>(null);
  const [popoverPos, setPopoverPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const handleMouseEnterFk = (e: React.MouseEvent, fk: ForeignKeyDetailDTO) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setPopoverPos({
      x: rect.left,
      y: rect.top - 8,
    });
    setActiveFkHover(fk);
  };

  const handleMouseLeaveFk = () => {
    setActiveFkHover(null);
  };

  return (
    <div
      style={{
        backgroundColor: tokens.surfacePrimary,
        borderRadius: '10px',
        border: `1px solid ${tokens.border}`,
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
        display: 'flex',
        flexDirection: 'column',
        height: '340px',
        position: 'relative',
        boxSizing: 'border-box',
        minWidth: 0,
      }}
    >
      {/* Table Header */}
      <div
        style={{
          padding: '12px 14px',
          borderBottom: `1px solid ${tokens.borderLight}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#FAFAFC',
          borderTopLeftRadius: '10px',
          borderTopRightRadius: '10px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', minWidth: 0 }}>
          <Table size={15} color={tokens.primaryAccent} style={{ flexShrink: 0 }} />
          <span
            style={{
              fontWeight: 700,
              fontSize: '0.86rem',
              color: tokens.textPrimary,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={table.name}
          >
            {table.name}
          </span>
        </div>
        <span
          style={{
            fontSize: '0.68rem',
            fontWeight: 600,
            color: tokens.textMuted,
            backgroundColor: '#EDF2F7',
            padding: '2px 6px',
            borderRadius: '4px',
            flexShrink: 0,
          }}
        >
          {table.column_count} cols
        </span>
      </div>

      {/* Columns List (Scrollable) */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '8px 12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '5px',
        }}
      >
        {table.columns.map((col: ColumnMetadataDTO) => {
          const isPk = col.primary_key;
          const fk = col.foreign_key;

          return (
            <div
              key={col.name}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '4px 6px',
                borderRadius: '4px',
                fontSize: '0.78rem',
                backgroundColor: isPk ? 'rgba(217, 119, 6, 0.04)' : (fk ? 'rgba(37, 99, 235, 0.03)' : 'transparent'),
                border: isPk ? '1px solid rgba(217, 119, 6, 0.15)' : '1px solid transparent',
              }}
            >
              {/* Column Name & Role Icon */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', minWidth: 0, flex: 1 }}>
                {isPk ? (
                  <Key size={12} color="#D97706" style={{ flexShrink: 0 }} />
                ) : fk ? (
                  <Link2 size={12} color={tokens.primaryAccent} style={{ flexShrink: 0 }} />
                ) : (
                  <span style={{ color: '#94A3B8', fontSize: '0.7rem', paddingLeft: '2px', flexShrink: 0 }}>•</span>
                )}

                <span
                  style={{
                    fontWeight: isPk ? 700 : 500,
                    color: isPk ? '#B45309' : tokens.textPrimary,
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                  title={`${col.name} (${col.type})`}
                >
                  {col.name}
                  {!col.nullable && <span style={{ color: '#DC2626', marginLeft: '2px' }}>*</span>}
                </span>

                {/* Foreign Key Badge (with Hover Tooltip Trigger) */}
                {fk && (
                  <div
                    onMouseEnter={(e) => handleMouseEnterFk(e, fk)}
                    onMouseLeave={handleMouseLeaveFk}
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '2px',
                      fontSize: '0.65rem',
                      fontWeight: 600,
                      color: tokens.primaryAccent,
                      backgroundColor: 'rgba(37, 99, 235, 0.08)',
                      border: '1px solid rgba(37, 99, 235, 0.2)',
                      borderRadius: '3px',
                      padding: '1px 5px',
                      cursor: 'pointer',
                      flexShrink: 0,
                    }}
                    title={`References ${fk.referred_table}.${fk.referred_column}`}
                  >
                    <span>→ {fk.referred_table}</span>
                  </div>
                )}
              </div>

              {/* Data Type */}
              <span
                style={{
                  fontSize: '0.68rem',
                  color: tokens.textMuted,
                  fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
                  marginLeft: '8px',
                  flexShrink: 0,
                }}
              >
                {col.type}
              </span>
            </div>
          );
        })}
      </div>

      {/* Card Footer */}
      <div
        style={{
          padding: '8px 14px',
          borderTop: `1px solid ${tokens.borderLight}`,
          backgroundColor: '#FAFAFC',
          fontSize: '0.7rem',
          color: table.foreign_relations_count > 0 ? tokens.primaryAccent : tokens.textMuted,
          fontWeight: 600,
          borderBottomLeftRadius: '10px',
          borderBottomRightRadius: '10px',
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
        }}
      >
        <Link2 size={12} />
        <span>
          {table.foreign_relations_count === 1
            ? '1 Foreign Relationship'
            : `${table.foreign_relations_count} Foreign Relationships`}
        </span>
      </div>

      {/* Floating Foreign Key Relationship Hover Tooltip / Popover */}
      {activeFkHover && (
        <div
          style={{
            position: 'fixed',
            left: `${popoverPos.x}px`,
            top: `${popoverPos.y}px`,
            transform: 'translateY(-100%)',
            zIndex: 9999,
            backgroundColor: '#0F172A',
            color: '#FFFFFF',
            borderRadius: '6px',
            padding: '8px 12px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.25)',
            fontSize: '0.74rem',
            lineHeight: 1.4,
            pointerEvents: 'none',
            minWidth: '180px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 700, color: '#38BDF8', marginBottom: '4px' }}>
            <Link2 size={12} />
            <span>Foreign Key Constraint</span>
          </div>
          <div style={{ color: '#94A3B8', fontSize: '0.68rem' }}>Source:</div>
          <div style={{ fontWeight: 600, color: '#F8FAFC', fontFamily: 'monospace' }}>
            {table.name}.{activeFkHover.constrained_column}
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', margin: '2px 0', color: '#38BDF8' }}>
            <ArrowDown size={13} />
          </div>
          <div style={{ color: '#94A3B8', fontSize: '0.68rem' }}>Referenced:</div>
          <div style={{ fontWeight: 600, color: '#34D399', fontFamily: 'monospace' }}>
            {activeFkHover.referred_table}.{activeFkHover.referred_column}
          </div>
        </div>
      )}
    </div>
  );
};
