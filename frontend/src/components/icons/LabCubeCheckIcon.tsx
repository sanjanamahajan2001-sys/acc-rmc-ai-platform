import React from 'react';
import { DomainIconProps } from './types';

export const LabCubeCheckIcon: React.FC<DomainIconProps> = ({
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
      {/* 3D Isometric Concrete Cube (150mm x 150mm) on Left */}
      {/* Top Face */}
      <path d="M22 14L36 21L22 28L8 21L22 14Z" fill="#CBD5E1" />
      {/* Left Face */}
      <path d="M8 21L22 28V46L8 39V21Z" fill="#64748B" />
      {/* Right Face */}
      <path d="M22 28L36 21V39L22 46V28Z" fill="#94A3B8" />
      {/* Cube Joint Edge Lines */}
      <path d="M22 14L36 21V39L22 46L8 39V21L22 14Z" stroke="#475569" strokeWidth="1.5" />
      <line x1="22" y1="28" x2="22" y2="46" stroke="#475569" strokeWidth="1.5" />

      {/* QA Inspection Clipboard on Right */}
      <rect x="30" y="20" width="26" height="36" rx="3" fill="#3B82F6" />
      <rect x="33" y="25" width="20" height="28" rx="1.5" fill="#FFFFFF" />
      {/* Clip Top */}
      <rect x="38" y="17" width="10" height="6" rx="1.5" fill="#1E293B" />
      <circle cx="43" cy="20" r="1.5" fill="#FFFFFF" />

      {/* Completed Checklist Rows */}
      {/* Row 1 */}
      <circle cx="37" cy="31" r="2" fill="#10B981" />
      <line x1="42" y1="31" x2="50" y2="31" stroke="#94A3B8" strokeWidth="1.5" strokeLinecap="round" />
      {/* Row 2 */}
      <circle cx="37" cy="38" r="2" fill="#10B981" />
      <line x1="42" y1="38" x2="49" y2="38" stroke="#94A3B8" strokeWidth="1.5" strokeLinecap="round" />
      {/* Row 3 */}
      <circle cx="37" cy="45" r="2" fill="#10B981" />
      <line x1="42" y1="45" x2="50" y2="45" stroke="#94A3B8" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
};
