import React from 'react';
import { DomainIconProps } from './types';

export const RupeeCoinIcon: React.FC<DomainIconProps> = ({
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
      {/* Outer Coin Edge Rim */}
      <circle cx="32" cy="32" r="26" fill="#D97706" />
      <circle cx="32" cy="32" r="24" fill="#F59E0B" />
      <circle cx="32" cy="32" r="22" fill="#FBBF24" />

      {/* Coin Center Surface */}
      <circle cx="32" cy="32" r="19" fill="#FDE68A" />

      {/* Bold Indian Rupee (₹) Symbol */}
      <path
        d="M23 19H41M23 25H38M23 19V32C28 32 35 32 35 25C35 20 28 19 28 19M28 32L40 45"
        stroke="#78350F"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};
