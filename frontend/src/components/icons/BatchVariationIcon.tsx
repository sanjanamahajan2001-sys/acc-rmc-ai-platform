import React from 'react';
import { DomainIconProps } from './types';

export const BatchVariationIcon: React.FC<DomainIconProps> = ({
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
      {/* Normal Distribution Bell Curve Area */}
      <path
        d="M8 50C16 50 20 48 24 38C28 26 30 14 32 14C34 14 36 26 40 38C44 48 48 50 56 50"
        stroke="#F97316"
        strokeWidth="3.5"
        strokeLinecap="round"
        fill="none"
      />
      <path
        d="M8 50C16 50 20 48 24 38C28 26 30 14 32 14C34 14 36 26 40 38C44 48 48 50 56 50H8Z"
        fill="#FFEDD5"
        opacity="0.45"
      />

      {/* Mean Axis Center Line */}
      <line x1="32" y1="14" x2="32" y2="52" stroke="#EA580C" strokeWidth="2" strokeDasharray="3 2" />

      {/* Standard Deviation Delta Arrows (± Sigma) */}
      <line x1="22" y1="36" x2="42" y2="36" stroke="#C2410C" strokeWidth="1.8" />
      <path d="M24 33L21 36L24 39" stroke="#C2410C" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M40 33L43 36L40 39" stroke="#C2410C" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />

      {/* Baseline */}
      <line x1="6" y1="52" x2="58" y2="52" stroke="#64748B" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
};
