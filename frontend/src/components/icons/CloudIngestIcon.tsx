import React from 'react';
import { DomainIconProps } from './types';

export const CloudIngestIcon: React.FC<DomainIconProps> = ({
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
      {/* Cloud Outline in Cerulean Blue */}
      <path
        d="M45 28C45 20.8 39.2 15 32 15C26 15 20.9 19.1 19.4 24.8C14.7 25.4 11 29.5 11 34.5C11 40 15.5 44.5 21 44.5H45C49.4 44.5 53 40.9 53 36.5C53 32.3 49.6 28.8 45.4 28.5L45 28Z"
        fill="#0284C7"
      />
      <path
        d="M44 29C44 22.5 38.6 17 32 17C26.5 17 21.8 20.8 20.4 26C16.2 26.5 13 30.2 13 34.7C13 39.5 17 43.5 22 43.5H44C48 43.5 51.5 40.2 51.5 36.2C51.5 32.4 48.5 29.3 44.7 29L44 29Z"
        fill="#38BDF8"
      />

      {/* Database Storage Platter under Cloud */}
      <ellipse cx="32" cy="48" rx="14" ry="4.5" fill="#0369A1" />
      <path d="M18 48V54C18 56.5 24.3 58.5 32 58.5C39.7 58.5 46 56.5 46 54V48" fill="#0284C7" stroke="#0369A1" strokeWidth="1" />
      <ellipse cx="32" cy="54" rx="14" ry="4" fill="#0284C7" />
      <ellipse cx="32" cy="48" rx="14" ry="4" fill="#38BDF8" />

      {/* Downward Data Ingest Arrow (White & Amber) */}
      <path
        d="M32 24V38M32 38L27 33M32 38L37 33"
        stroke="#FFFFFF"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};
