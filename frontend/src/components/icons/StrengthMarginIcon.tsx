import React from 'react';
import { DomainIconProps } from './types';

export const StrengthMarginIcon: React.FC<DomainIconProps> = ({
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
      {/* Background Circular Shield Tone */}
      <circle cx="32" cy="32" r="26" fill="#F0FDF4" stroke="#DCFCE7" strokeWidth="2" />

      {/* Upward Growth Bars */}
      <rect x="14" y="40" width="7" height="12" rx="1.5" fill="#BBF7D0" />
      <rect x="25" y="32" width="7" height="20" rx="1.5" fill="#86EFAC" />
      <rect x="36" y="24" width="7" height="28" rx="1.5" fill="#4ADE80" />
      <rect x="47" y="16" width="7" height="36" rx="1.5" fill="#16A34A" />

      {/* Dynamic Rising Arrow */}
      <path
        d="M12 36L26 23L36 30L51 12"
        stroke="#15803D"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M40 12H52V24"
        stroke="#15803D"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Plus Sign / Margin Indicator Badge */}
      <circle cx="21" cy="18" r="6" fill="#059669" />
      <path d="M21 15V21M18 18H24" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
};
