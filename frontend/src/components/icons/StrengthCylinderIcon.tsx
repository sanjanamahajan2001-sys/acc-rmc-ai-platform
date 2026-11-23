import React from 'react';
import { DomainIconProps } from './types';

export const StrengthCylinderIcon: React.FC<DomainIconProps> = ({
  size = 20,
  className = '',
  style = {},
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={{ display: 'inline-block', verticalAlign: 'middle', flexShrink: 0, ...style }}
    >
      {/* Hydraulic Press Base Machine */}
      <rect x="8" y="52" width="48" height="6" rx="2" fill="#1E293B" />
      {/* Bottom Steel Bearing Platen */}
      <rect x="18" y="48" width="28" height="4" rx="1" fill="#475569" />

      {/* Hydraulic Compression Frame Columns */}
      <rect x="10" y="12" width="5" height="40" rx="1.5" fill="#64748B" />
      <rect x="49" y="12" width="5" height="40" rx="1.5" fill="#64748B" />

      {/* Top Crosshead Beam */}
      <rect x="8" y="8" width="48" height="8" rx="2" fill="#1E293B" />
      {/* Upper Hydraulic Ram & Platen */}
      <rect x="28" y="16" width="8" height="6" fill="#334155" />
      <rect x="20" y="22" width="24" height="4" rx="1" fill="#475569" />

      {/* Concrete Test Specimen Cylinder (150mm x 300mm Standard) */}
      <rect x="22" y="26" width="20" height="22" fill="#94A3B8" />
      <ellipse cx="32" cy="26" rx="10" ry="2.5" fill="#CBD5E1" />
      <ellipse cx="32" cy="48" rx="10" ry="2.5" fill="#64748B" />
      {/* Concrete Texture Specks */}
      <circle cx="27" cy="32" r="1" fill="#475569" />
      <circle cx="35" cy="35" r="1.2" fill="#475569" />
      <circle cx="29" cy="41" r="1" fill="#475569" />
      <circle cx="37" cy="43" r="0.8" fill="#475569" />

      {/* Golden Badge of Compliance on Side */}
      <circle cx="46" cy="36" r="9" fill="#F59E0B" />
      <circle cx="46" cy="36" r="7.5" fill="#FFFFFF" />
      <path
        d="M42 36L45 39L50 33"
        stroke="#10B981"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};
