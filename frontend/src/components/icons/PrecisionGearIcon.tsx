import React from 'react';
import { DomainIconProps } from './types';

export const PrecisionGearIcon: React.FC<DomainIconProps> = ({
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
      {/* Outer Gear Teeth Wheel */}
      <path
        d="M27 7H37V12.2C38.7 12.7 40.4 13.4 42 14.3L46 10.9L53.1 18L49.7 22C50.6 23.6 51.3 25.3 51.8 27H57V37H51.8C51.3 38.7 50.6 40.4 49.7 42L53.1 46L46 53.1L42 49.7C40.4 50.6 38.7 51.3 37 51.8V57H27V51.8C25.3 51.3 23.6 50.6 22 49.7L18 53.1L10.9 46L14.3 42C13.4 40.4 12.7 38.7 12.2 37H7V27H12.2C12.7 25.3 13.4 23.6 14.3 22L10.9 18L18 10.9L22 14.3C23.6 13.4 25.3 12.7 27 12.2V7Z"
        fill="#334155"
      />
      <circle cx="32" cy="32" r="20" fill="#475569" />
      <circle cx="32" cy="32" r="16" fill="#64748B" />

      {/* Chrome Inner Ring */}
      <circle cx="32" cy="32" r="11" fill="#CBD5E1" />
      <circle cx="32" cy="32" r="8" fill="#1E293B" />
      <circle cx="32" cy="32" r="4" fill="#0EA5E9" />
    </svg>
  );
};
