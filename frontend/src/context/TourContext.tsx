/**
 * TourContext & TourProvider — Centralized Tour State Management.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import {
  TourStep,
  INITIAL_TOUR_STEPS,
  hasUserCompletedTour,
  markUserTourCompleted,
  resetUserTour,
} from '../services/tourService';
import { PlatformTourOverlay } from '../components/tour/PlatformTourOverlay';

interface TourContextType {
  isTourActive: boolean;
  currentStepIndex: number;
  currentStep: TourStep | null;
  totalSteps: number;
  startTour: (steps?: TourStep[]) => void;
  endTour: () => void;
  nextStep: () => void;
  prevStep: () => void;
  resetTourStatus: () => void;
}

const TourContext = createContext<TourContextType | undefined>(undefined);

export const TourProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [steps, setSteps] = useState<TourStep[]>(INITIAL_TOUR_STEPS);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [isTourActive, setIsTourActive] = useState<boolean>(false);

  const userId = user?.id || user?.username || 'admin';

  // Auto-launch on first login
  useEffect(() => {
    if (!isAuthenticated) {
      setIsTourActive(false);
      return;
    }

    const completed = hasUserCompletedTour(userId);
    if (!completed) {
      // Auto launch after initial mount delay
      const timer = setTimeout(() => {
        setIsTourActive(true);
        setCurrentStepIndex(0);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [isAuthenticated, userId]);

  const startTour = (customSteps?: TourStep[]) => {
    const activeSteps = customSteps || INITIAL_TOUR_STEPS;
    setSteps(activeSteps);
    setCurrentStepIndex(0);
    setIsTourActive(true);

    // Route to first step's route if different
    if (activeSteps.length > 0 && activeSteps[0].route && location.pathname !== activeSteps[0].route) {
      navigate(activeSteps[0].route);
    }
  };

  const endTour = () => {
    setIsTourActive(false);
    markUserTourCompleted(userId);
  };

  const resetTourStatus = () => {
    resetUserTour(userId);
    startTour();
  };

  const nextStep = () => {
    if (currentStepIndex >= steps.length - 1) {
      endTour();
      return;
    }

    const nextIdx = currentStepIndex + 1;
    const targetStep = steps[nextIdx];

    if (targetStep && targetStep.route && location.pathname !== targetStep.route) {
      navigate(targetStep.route);
    }

    setCurrentStepIndex(nextIdx);
  };

  const prevStep = () => {
    if (currentStepIndex <= 0) return;

    const prevIdx = currentStepIndex - 1;
    const targetStep = steps[prevIdx];

    if (targetStep && targetStep.route && location.pathname !== targetStep.route) {
      navigate(targetStep.route);
    }

    setCurrentStepIndex(prevIdx);
  };

  const currentStep = isTourActive && steps[currentStepIndex] ? steps[currentStepIndex] : null;

  return (
    <TourContext.Provider
      value={{
        isTourActive,
        currentStepIndex,
        currentStep,
        totalSteps: steps.length,
        startTour,
        endTour,
        nextStep,
        prevStep,
        resetTourStatus,
      }}
    >
      {children}
      <PlatformTourOverlay />
    </TourContext.Provider>
  );
};

export const useTour = (): TourContextType => {
  const context = useContext(TourContext);
  if (!context) {
    throw new Error('useTour must be used within a TourProvider');
  }
  return context;
};
