import React from 'react';
import { DomainIconProps } from './types';

export const PersonnelBadgeIcon: React.FC<DomainIconProps> = ({
  size = 18,
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
      {/* Blue Lanyard Strap Top */}
      <path d="M26 4L32 14L38 4" stroke="#2563EB" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      {/* Metal Clip */}
      <rect x="29" y="12" width="6" height="5" rx="1" fill="#94A3B8" />

      {/* Security ID Badge Card */}
      <rect x="14" y="16" width="36" height="44" rx="4" fill="#FFFFFF" stroke="#CBD5E1" strokeWidth="1.5" />
      {/* Top Header Strip (Safety Orange / Gold) */}
      <path d="M14 20C14 17.8 15.8 16 18 16H46C48.2 16 50 17.8 50 20V23H14V20Z" fill="#EA580C" />
      {/* Clip Hole */}
      <rect x="28" y="18" width="8" height="2" rx="1" fill="#FFFFFF" />

      {/* User Photo Box */}
      <rect x="18" y="27" width="13" height="15" rx="1.5" fill="#E2E8F0" />
      {/* Silhouette Head & Shoulders */}
      <circle cx="24.5" cy="32" r="3.5" fill="#64748B" />
      <path d="M19 41C19 38 21.5 37 24.5 37C27.5 37 30 38 30 41H19Z" fill="#475569" />

      {/* Identity Text Rows */}
      <rect x="34" y="28" width="12" height="2.5" rx="0.5" fill="#1E293B" />
      <rect x="34" y="33" width="9" height="2" rx="0.5" fill="#64748B" />
      <rect x="34" y="38" width="11" height="2" rx="0.5" fill="#94A3B8" />

      {/* Role / Access Clearance Bar */}
      <rect x="18" y="47" width="28" height="3" rx="1" fill="#10B981" />
      <rect x="18" y="52" width="16" height="2" rx="0.5" fill="#CBD5E1" />
    </svg>
  );
};
