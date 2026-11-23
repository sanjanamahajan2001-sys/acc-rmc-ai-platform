import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatisticalSummaryCards } from "../components/dashboard/sqc/StatisticalSummaryCards";
import { StrengthDistributionChart } from "../components/dashboard/sqc/StrengthDistributionChart";
import { MixPerformanceMatrix } from "../components/dashboard/sqc/MixPerformanceMatrix";
import { StrengthTrendTimeline } from "../components/dashboard/sqc/StrengthTrendTimeline";
import { DashboardFilterBar } from "../components/dashboard/DashboardFilterBar";
import {
  StrengthDistributionDTO,
  MixPerformanceListDTO,
  StrengthTimelineListDTO,
  FilterOptionsDTO,
} from "../services/reportingService";

describe("WS-DASH-2B Frontend SQC Components Test Suite", () => {
  const mockDistribution: StrengthDistributionDTO = {
    total_tested_batches: 1324,
    total_tested_specimens: 1394,
    mean_strength_mpa: 38.47,
    median_strength_mpa: 38.53,
    standard_deviation_mpa: 7.4,
    coefficient_of_variation_pct: 19.24,
    min_strength_mpa: 15.2,
    max_strength_mpa: 61.2,
    characteristic_strength_fck_mpa: 40.0,
    target_mean_strength_fck_prime_mpa: 48.25,
    strength_margin_mpa: -1.53,
    compliance_rate_pct: 88.8,
    stability_grade: "HIGH_VARIATION",
    histogram_bins: [
      { bin_start: 15.0, bin_end: 17.5, bin_label: "15.0–17.5", count: 5, is_below_fck: true },
      { bin_start: 40.0, bin_end: 42.5, bin_label: "40.0–42.5", count: 120, is_below_fck: false },
    ],
    scope_metadata: {
      plant_code: null,
      recipe_code: null,
      date_from: null,
      date_to: null,
      cache_token_version: 1,
      generated_at: "2026-09-17T11:00:00Z",
    },
  };

  const mockMixPerformance: MixPerformanceListDTO = {
    items: [
      {
        recipe_code: "M-30",
        recipe_name: "M-30 Standard Mix",
        grade: "M-30",
        target_strength_fck: 30.0,
        target_mean_strength_fck_prime: 38.25,
        total_batches: 752,
        tested_batches_28d: 515,
        tested_specimens_28d: 540,
        mean_strength_mpa: 40.54,
        standard_deviation_mpa: 3.2,
        coefficient_of_variation_pct: 7.89,
        strength_margin_mpa: 10.54,
        compliance_rate_pct: 98.8,
        stability_status: "EXCELLENT",
      },
    ],
    total_recipes_evaluated: 1,
    scope_metadata: {
      plant_code: null,
      recipe_code: null,
      date_from: null,
      date_to: null,
      cache_token_version: 1,
      generated_at: "2026-09-17T11:00:00Z",
    },
  };

  const mockTimeline: StrengthTimelineListDTO = {
    timeline: [
      {
        batch_number: "BATCH-TEST-001",
        plant_code: "PLANT-01",
        recipe_code: "M-30",
        grade: "M-30",
        production_timestamp: "2026-09-17 10:00",
        result_7d_mpa: 28.5,
        result_28d_mpa: 41.2,
        target_fck_mpa: 30.0,
        target_fck_prime_mpa: 38.25,
        is_compliant_28d: true,
      },
      {
        batch_number: "BATCH-TEST-002",
        plant_code: "PLANT-01",
        recipe_code: "M-30",
        grade: "M-30",
        production_timestamp: "2026-09-17 10:30",
        result_7d_mpa: 27.0,
        result_28d_mpa: null,
        target_fck_mpa: 30.0,
        target_fck_prime_mpa: 38.25,
        is_compliant_28d: null,
      },
    ],
    total_points: 2,
    scope_metadata: {
      plant_code: null,
      recipe_code: null,
      date_from: null,
      date_to: null,
      cache_token_version: 1,
      generated_at: "2026-09-17T11:00:00Z",
    },
  };

  const mockFilterOptions: FilterOptionsDTO = {
    plants: [{ plant_code: "PLANT-01", plant_name: "Mumbai Plant" }],
    recipes: [{ recipe_code: "M-30", recipe_name: "M-30 Mix", grade: "M-30", target_strength_mpa: 30.0 }],
    available_date_range: { earliest_date: "2026-01-01", latest_date: "2026-09-17" },
  };

  it("1. renders exact backend statistical values in StatisticalSummaryCards", () => {
    render(<StatisticalSummaryCards data={mockDistribution} isLoading={false} />);
    expect(screen.getByText("38.5")).toBeInTheDocument();
    expect(screen.getByText("40.0")).toBeInTheDocument();
    expect(screen.getByText("-1.5")).toBeInTheDocument();
    expect(screen.getByText("HIGH VARIATION")).toBeInTheDocument();
    expect(screen.getByText("1,324")).toBeInTheDocument();
  });

  it("2. renders clean empty state in StatisticalSummaryCards when data is null", () => {
    render(<StatisticalSummaryCards data={null} isLoading={false} />);
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
    expect(screen.getByText("0")).toBeInTheDocument();
  });

  it("3. renders StrengthDistributionChart with backend histogram bins and responsive layout", () => {
    const { container } = render(<StrengthDistributionChart data={mockDistribution} isLoading={false} />);
    expect(screen.getByText("28-Day Strength Distribution Histogram")).toBeInTheDocument();
    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.getByText("40")).toBeInTheDocument();
    expect(container.querySelector(".dashboard-contained-scroll")).toBeInTheDocument();
  });

  it("4. renders MixPerformanceMatrix with responsive scroll wrapper", () => {
    const { container } = render(<MixPerformanceMatrix data={mockMixPerformance} isLoading={false} />);
    expect(screen.getByText("M-30")).toBeInTheDocument();
    expect(screen.getByText("40.5 MPa")).toBeInTheDocument();
    expect(screen.getByText("+10.5 MPa")).toBeInTheDocument();
    expect(screen.getByText("98.8%")).toBeInTheDocument();
    expect(screen.getByText("Controlled")).toBeInTheDocument();
    expect(container.querySelector(".dashboard-contained-scroll")).toBeInTheDocument();
  });

  it("5. renders StrengthTrendTimeline with clarified recent progression title and pending curing indicator", () => {
    const { container } = render(<StrengthTrendTimeline data={mockTimeline} isLoading={false} />);
    expect(screen.getByText("Recent Batch Strength Progression (Last 50 Batches)")).toBeInTheDocument();
    expect(screen.getByText("BATCH-TEST-001")).toBeInTheDocument();
    expect(screen.getByText("41.2 MPa")).toBeInTheDocument();
    expect(screen.getByText("Pass")).toBeInTheDocument();
    expect(screen.getByText("BATCH-TEST-002")).toBeInTheDocument();
    expect(screen.getByText("Pending 28D")).toBeInTheDocument();
    expect(screen.getByText("Curing")).toBeInTheDocument();
    expect(container.querySelector(".dashboard-contained-scroll")).toBeInTheDocument();
  });

  it("6. renders DashboardFilterBar with responsive layout and stacked inputs", () => {
    const { container } = render(
      <DashboardFilterBar
        filterOptions={mockFilterOptions}
        selectedPlant=""
        selectedRecipe=""
        dateFrom=""
        dateTo=""
        onPlantChange={vi.fn()}
        onRecipeChange={vi.fn()}
        onDateFromChange={vi.fn()}
        onDateToChange={vi.fn()}
        onResetFilters={vi.fn()}
        isLoading={false}
      />
    );
    expect(container.querySelector(".dashboard-filter-bar-container")).toBeInTheDocument();
    expect(screen.getByText("Plant Scope:")).toBeInTheDocument();
    expect(screen.getByText("Mix Design:")).toBeInTheDocument();
    expect(screen.getByText("Production Date:")).toBeInTheDocument();
  });
});
