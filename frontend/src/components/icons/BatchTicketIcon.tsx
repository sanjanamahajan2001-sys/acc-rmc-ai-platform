import React from 'react';
import { DomainIconProps } from './types';

export const BatchTicketIcon: React.FC<DomainIconProps> = ({
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
      {/* Clipboard Backboard (Industrial Hardboard) */}
      <rect x="12" y="10" width="40" height="48" rx="4" fill="#334155" />
      {/* Top Metallic Clamp */}
      <rect x="22" y="6" width="20" height="8" rx="2" fill="#94A3B8" />
      <circle cx="32" cy="10" r="2.5" fill="#1E293B" />

      {/* Official White Delivery Batch Ticket Paper */}
      <rect x="16" y="14" width="32" height="40" rx="2" fill="#FFFFFF" />

      {/* Ticket Header (ACC Blue Bar) */}
      <rect x="19" y="18" width="26" height="4" rx="1" fill="#2563EB" />

      {/* Concrete Batch Details Lines */}
      <rect x="19" y="26" width="14" height="2" rx="0.5" fill="#64748B" />
      <rect x="36" y="26" width="9" height="2" rx="0.5" fill="#10B981" />

      <rect x="19" y="31" width="18" height="2" rx="0.5" fill="#94A3B8" />
      <rect x="19" y="36" width="12" height="2" rx="0.5" fill="#94A3B8" />

      {/* Digital Barcode on Bottom of Ticket */}
      <rect x="19" y="42" width="2" height="7" fill="#1E293B" />
      <rect x="22" y="42" width="1" height="7" fill="#1E293B" />
      <rect x="24" y="42" width="3" height="7" fill="#1E293B" />
      <rect x="28" y="42" width="1.5" height="7" fill="#1E293B" />
      <rect x="31" y="42" width="2.5" height="7" fill="#1E293B" />
      <rect x="35" y="42" width="1" height="7" fill="#1E293B" />
      <rect x="37" y="42" width="2" height="7" fill="#1E293B" />

      {/* Green Dispatch Stamp */}
      <circle cx="41" cy="38" r="6" fill="#10B981" />
      <path d="M38 38L40 40L44 36" stroke="#FFFFFF" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
};
