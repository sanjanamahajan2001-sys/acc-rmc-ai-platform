/**
 * PlatformTourOverlay — Interactive Spotlight & Coachmark Popover Component.
 */

import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useTour } from '../../context/TourContext';
import { CATEGORY_THEMES, CategoryTheme } from '../../services/tourService';
import { ChevronLeft, ChevronRight, X, Sparkles } from 'lucide-react';

export const PlatformTourOverlay: React.FC = () => {
  const { isTourActive, currentStep, currentStepIndex, totalSteps, nextStep, prevStep, endTour } = useTour();

  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const [popoverPos, setPopoverPos] = useState<{ top: number; left: number }>({ top: 100, left: 100 });
  const popoverRef = useRef<HTMLDivElement>(null);

  const theme: CategoryTheme =
    currentStep && CATEGORY_THEMES[currentStep.category]
      ? CATEGORY_THEMES[currentStep.category]
      : CATEGORY_THEMES['Platform Overview'];

  const updatePosition = useCallback(() => {
    if (!currentStep) return;

    const el = document.querySelector(currentStep.targetSelector);
    if (!el) {
      setTargetRect(null);
      setPopoverPos({
        top: window.innerHeight / 2 - 120,
        left: window.innerWidth / 2 - 210,
      });
      return;
    }

    // Smooth scroll target element into viewport
    el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });

    const rect = el.getBoundingClientRect();
    setTargetRect(rect);

    const popoverWidth = 420;
    const popoverHeight = popoverRef.current ? popoverRef.current.offsetHeight : 220;
    const padding = 16;

    let top = rect.bottom + padding;
    let left = rect.left + rect.width / 2 - popoverWidth / 2;

    // Viewport boundaries
    if (left < 16) left = 16;
    if (left + popoverWidth > window.innerWidth - 16) {
      left = window.innerWidth - popoverWidth - 16;
    }

    if (top + popoverHeight > window.innerHeight - 16) {
      top = rect.top - popoverHeight - padding;
      if (top < 16) top = 16;
    }

    setPopoverPos({ top, left });
  }, [currentStep]);

  useEffect(() => {
    if (!isTourActive || !currentStep) return;

    const timer = setTimeout(updatePosition, 180);

    const handleResize = () => updatePosition();
    const handleScroll = () => updatePosition();

    window.addEventListener('resize', handleResize);
    window.addEventListener('scroll', handleScroll, true);

    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('scroll', handleScroll, true);
    };
  }, [isTourActive, currentStep, updatePosition]);

  if (!isTourActive || !currentStep) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        pointerEvents: 'auto',
      }}
    >
      {/* SVG Spotlight Cutout Mask */}
      <svg
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
        }}
      >
        <defs>
          <mask id="spotlight-mask">
            <rect x="0" y="0" width="100%" height="100%" fill="#FFFFFF" />
            {targetRect && (
              <rect
                x={targetRect.left - 6}
                y={targetRect.top - 6}
                width={targetRect.width + 12}
                height={targetRect.height + 12}
                rx="8"
                ry="8"
                fill="#000000"
              />
            )}
          </mask>
        </defs>

        {/* Backdrop Mask */}
        <rect
          x="0"
          y="0"
          width="100%"
          height="100%"
          fill="rgba(15, 23, 42, 0.68)"
          mask="url(#spotlight-mask)"
        />

        {/* Dynamic Category Themed Spotlight Border Glow */}
        {targetRect && (
          <rect
            x={targetRect.left - 6}
            y={targetRect.top - 6}
            width={targetRect.width + 12}
            height={targetRect.height + 12}
            rx="8"
            ry="8"
            fill="none"
            stroke={theme.primary}
            strokeWidth="2.5"
            style={{
              filter: `drop-shadow(0 0 10px ${theme.glow})`,
              transition: 'all 0.25s ease-in-out',
            }}
          />
        )}
      </svg>

      {/* Floating Popover Coachmark Card */}
      <div
        ref={popoverRef}
        style={{
          position: 'absolute',
          top: `${popoverPos.top}px`,
          left: `${popoverPos.left}px`,
          width: '420px',
          maxWidth: 'calc(100vw - 32px)',
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          borderTop: `4px solid ${theme.primary}`,
          borderRight: '1px solid #E2E8F0',
          borderBottom: '1px solid #CBD5E1',
          borderLeft: '1px solid #E2E8F0',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.25), 0 8px 10px -6px rgba(0, 0, 0, 0.2)',
          padding: '18px 20px',
          zIndex: 10000,
          fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
          boxSizing: 'border-box',
          transition: 'top 0.2s ease-out, left 0.2s ease-out',
        }}
      >
        {/* Header: Category Badge & Close X */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '10px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Sparkles size={14} color={theme.primary} />
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                color: theme.primary,
                backgroundColor: theme.bgLight,
                padding: '3px 8px',
                borderRadius: '4px',
                letterSpacing: '0.03em',
                textTransform: 'uppercase',
              }}
            >
              {currentStep.badge || theme.tag}
            </span>
          </div>

          <button
            type="button"
            onClick={endTour}
            aria-label="Close tour"
            title="Skip tour"
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: '#94A3B8',
              padding: '4px',
              display: 'flex',
              alignItems: 'center',
              borderRadius: '4px',
            }}
          >
            <X size={16} />
          </button>
        </div>

        {/* Title */}
        <h4
          style={{
            fontSize: '0.96rem',
            fontWeight: 800,
            color: '#0F172A',
            margin: '0 0 6px 0',
            letterSpacing: '-0.01em',
          }}
        >
          {currentStep.title}
        </h4>

        {/* Description / Instruction */}
        <p
          style={{
            fontSize: '0.82rem',
            color: '#475569',
            lineHeight: 1.48,
            margin: '0 0 16px 0',
          }}
        >
          {currentStep.content}
        </p>

        {/* Footer Actions: Progress Counter, Back, Next / Finish */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            paddingTop: '12px',
            borderTop: '1px solid #F1F5F9',
          }}
        >
          {/* Progress Counter & Track */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: 0 }}>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                color: '#64748B',
                whiteSpace: 'nowrap',
              }}
            >
              {currentStepIndex + 1} / {totalSteps}
            </span>
            <div
              style={{
                flex: 1,
                height: '5px',
                backgroundColor: '#E2E8F0',
                borderRadius: '3px',
                overflow: 'hidden',
                maxWidth: '120px',
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${((currentStepIndex + 1) / totalSteps) * 100}%`,
                  backgroundColor: theme.primary,
                  borderRadius: '3px',
                  transition: 'width 0.2s ease-in-out',
                }}
              />
            </div>
          </div>

          {/* Navigation Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
            {currentStepIndex > 0 && (
              <button
                type="button"
                onClick={prevStep}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '4px',
                  backgroundColor: '#F8FAFC',
                  border: '1px solid #CBD5E1',
                  color: '#475569',
                  borderRadius: '6px',
                  padding: '6px 12px',
                  fontSize: '0.8rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  flexShrink: 0,
                  transition: 'all 0.15s ease',
                }}
              >
                <ChevronLeft size={14} />
                <span>Back</span>
              </button>
            )}

            <button
              type="button"
              onClick={nextStep}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '5px',
                backgroundColor: theme.primary,
                border: 'none',
                color: '#FFFFFF',
                borderRadius: '6px',
                padding: '6px 14px',
                fontSize: '0.8rem',
                fontWeight: 700,
                cursor: 'pointer',
                boxShadow: `0 2px 4px 0 ${theme.glow}`,
                whiteSpace: 'nowrap',
                flexShrink: 0,
                transition: 'background-color 0.15s ease-in-out',
              }}
            >
              <span>{currentStepIndex === totalSteps - 1 ? 'Finish' : 'Next'}</span>
              {currentStepIndex < totalSteps - 1 && <ChevronRight size={14} style={{ flexShrink: 0 }} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
