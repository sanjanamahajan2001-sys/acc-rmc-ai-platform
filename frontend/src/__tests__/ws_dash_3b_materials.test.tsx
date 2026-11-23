import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MaterialSummaryCards } from "../components/dashboard/materials/MaterialSummaryCards";
import { MaterialConsumptionMatrix } from "../components/dashboard/materials/MaterialConsumptionMatrix";
import { BatchWeighingVarianceChart } from "../components/dashboard/materials/BatchWeighingVarianceChart";
import { WaterCementRatioChart } from "../components/dashboard/materials/WaterCementRatioChart";
import { BinderIntensityMatrix } from "../components/dashboard/materials/BinderIntensityMatrix";
import { MixPerformanceMatrix } from "../components/dashboard/sqc/MixPerformanceMatrix";
import {
  MaterialConsumptionSummaryDTO,
  BatchVarianceAnalysisDTO,
  BinderEfficiencyDTO,
  MixPerformanceListDTO,
} from "../services/reportingService";

describe("WS-DASH-3B Material Consumption, Batch Variance & Binder Intensity Test Suite", () => {
  const mockMaterialSummary: MaterialConsumptionSummaryDTO = {
    total_batches: 1699,
    total_produced_batches: 1699,
    total_scheduled_batches: 199,
    material_consumption_batch_count: 1699,
    total_volume_m3: 4366.0,
    total_planned_material_kg: 10245000.0,
    total_actual_material_kg: 10280000.0,
    total_variance_kg: 35000.0,
    overall_variance_percentage: 0.34,
    total_binder_consumption_kg: 1850000.0,
    total_water_consumption_kg: 720000.0,
    total_aggregate_consumption_kg: 7650000.0,
    total_admixture_consumption_kg: 60000.0,
    scope_metadata: {
      plant_code: "PLANT-MUM-01",
      recipe_code: null,
      date_from: null,
      date_to: null,
      cache_token_version: 1,
      generated_at: "2026-09-17T12:00:00Z",
    },
    items: [
      {
        material_code: "CEMENT_OPC",
        material_name: "OPC 53 Grade Cement",
        category: "CEMENT",
        broad_category: "BINDER",
        record_count: 1699,
        batch_count: 1699,
        planned_quantity_kg: 1400000.0,
        actual_quantity_kg: 1405000.0,
        variance_quantity_kg: 5000.0,
        variance_percentage: 0.36,
        avg_consumption_per_batch_kg: 826.96,
        consumption_kg_per_m3: 321.8,
        engineering_unit: "kg",
      },
      {
        material_code: "GGBS",
        material_name: "Ground Granulated Blast-Furnace Slag",
        category: "GGBS",
        broad_category: "MINERAL_ADMIXTURE",
        record_count: 1699,
        batch_count: 1699,
        planned_quantity_kg: 450000.0,
        actual_quantity_kg: 445000.0,
        variance_quantity_kg: -5000.0,
        variance_percentage: -1.11,
        avg_consumption_per_batch_kg: 261.92,
        consumption_kg_per_m3: 101.9,
        engineering_unit: "kg",
      },
      {
        material_code: "WATER",
        material_name: "Mixing Water",
        category: "WATER",
        broad_category: "WATER",
        record_count: 1699,
        batch_count: 1699,
        planned_quantity_kg: 700000.0,
        actual_quantity_kg: 720000.0,
        variance_quantity_kg: 20000.0,
        variance_percentage: 2.86,
        avg_consumption_per_batch_kg: 423.78,
        consumption_kg_per_m3: 164.9,
        engineering_unit: "kg",
      },
    ],
  };

  const mockBatchVariance: BatchVarianceAnalysisDTO = {
    overall_summary: {
      indicator_name: "IS 4926:2003 Annex E Weighment Tolerance Indicator",
      total_weighments: 8273,
      classifiable_weighments: 8270,
      compliant_weighments: 7720,
      non_compliant_weighments: 550,
      annex_e_compliance_rate_pct: 93.35,
      mean_abs_variance_pct: 1.12,
      annex_e_weighment_batch_count: 1699,
      unclassified_record_count: 3,
      unclassified_material_codes: ["UNKNOWN_FIBER_X"],
      standard_applied: "IS 4926:2003 Annex E / Clause E-1",
    },
    categories: [
      {
        category_code: "BINDER",
        category_name: "Cement & Binders",
        compliance_status: "CLASSIFIABLE",
        is4926_tolerance_pct: 2.0,
        record_count: 1699,
        compliant_count: 1620,
        non_compliant_count: 79,
        compliance_rate_pct: 95.35,
        planned_total_kg: 1400000.0,
        actual_total_kg: 1405000.0,
        variance_total_kg: 5000.0,
        mean_variance_pct: 0.36,
        mean_abs_variance_pct: 0.85,
        max_abs_variance_pct: 2.9,
        materials: [
          {
            material_code: "CEMENT_OPC",
            material_name: "OPC 53 Grade Cement",
            compliance_status: "CLASSIFIABLE",
            is4926_tolerance_pct: 2.0,
            record_count: 1699,
            compliant_count: 1620,
            non_compliant_count: 79,
            compliance_rate_pct: 95.35,
            planned_quantity_kg: 1400000.0,
            actual_quantity_kg: 1405000.0,
            variance_quantity_kg: 5000.0,
            mean_variance_pct: 0.36,
            mean_abs_variance_pct: 0.85,
            max_abs_variance_pct: 2.9,
          },
        ],
      },
      {
        category_code: "UNKNOWN",
        category_name: "Unclassified Materials",
        compliance_status: "NOT_CLASSIFIABLE",
        is4926_tolerance_pct: null,
        record_count: 3,
        compliant_count: 0,
        non_compliant_count: 0,
        compliance_rate_pct: null,
        planned_total_kg: 300.0,
        actual_total_kg: 305.0,
        variance_total_kg: 5.0,
        mean_variance_pct: 1.67,
        mean_abs_variance_pct: 1.67,
        max_abs_variance_pct: 1.8,
        materials: [
          {
            material_code: "UNKNOWN_FIBER_X",
            material_name: "Specialty Fiber",
            compliance_status: "NOT_CLASSIFIABLE",
            is4926_tolerance_pct: null,
            record_count: 3,
            compliant_count: 0,
            non_compliant_count: 0,
            compliance_rate_pct: null,
            planned_quantity_kg: 300.0,
            actual_quantity_kg: 305.0,
            variance_quantity_kg: 5.0,
            mean_variance_pct: 1.67,
            mean_abs_variance_pct: 1.67,
            max_abs_variance_pct: 1.8,
          },
        ],
      },
    ],
    water_moisture_analysis: {
      planned_water_kg: 700000.0,
      actual_water_kg: 720000.0,
      raw_water_variance_kg: 20000.0,
      raw_water_variance_pct: 2.86,
      moisture_probe_records_count: 0,
      total_water_records_count: 1699,
      data_quality_status: "LIMITED",
      operational_note:
        "Raw water variance reflects scale delivery and operational moisture compensation; moisture-corrected target unavailable.",
    },
    scope_metadata: {
      plant_code: "PLANT-MUM-01",
      recipe_code: null,
      date_from: null,
      date_to: null,
      cache_token_version: 1,
      generated_at: "2026-09-17T12:00:00Z",
    },
  };

  const mockBinderEfficiency: BinderEfficiencyDTO = {
    fleet_summary: {
      total_evaluated_recipes: 2,
      total_production_batches: 1699,
      total_tested_batches_28d: 1165,
      tested_28d_batch_count: 1165,
      fleet_avg_cement_kg_m3: 312.4,
      fleet_avg_binder_kg_m3: 415.8,
      fleet_avg_actual_wb: 0.395,
      fleet_avg_actual_wc: 0.528,
      fleet_avg_28d_strength_mpa: 42.1,
      fleet_avg_binder_intensity: 9.89,
    },
    recipes: [
      {
        recipe_code: "M-30",
        grade: "M-30",
        target_strength_fck_mpa: 30.0,
        total_batches: 1200,
        tested_batches_28d: 850,
        tested_specimens_28d: 890,
        cement_content_kg_m3: 280.0,
        total_binder_content_kg_m3: 380.0,
        water_content_kg_m3: 155.0,
        actual_wb_ratio: 0.408,
        planned_wb_ratio: 0.400,
        actual_wc_ratio: 0.554,
        mean_28d_strength_mpa: 40.5,
        min_28d_strength_mpa: 32.0,
        max_28d_strength_mpa: 48.0,
        binder_intensity_index_kg_m3_per_mpa: 9.38,
        cement_intensity_index_kg_m3_per_mpa: 6.91,
        is_statistically_reliable: true,
        sample_size_status: "RELIABLE",
      },
      {
        recipe_code: "M-50-SPECIAL",
        grade: "M-50",
        target_strength_fck_mpa: 50.0,
        total_batches: 15,
        tested_batches_28d: 4,
        tested_specimens_28d: 4,
        cement_content_kg_m3: 420.0,
        total_binder_content_kg_m3: 540.0,
        water_content_kg_m3: 160.0,
        actual_wb_ratio: 0.296,
        planned_wb_ratio: 0.290,
        actual_wc_ratio: 0.381,
        mean_28d_strength_mpa: 58.2,
        min_28d_strength_mpa: 54.0,
        max_28d_strength_mpa: 62.0,
        binder_intensity_index_kg_m3_per_mpa: 9.28,
        cement_intensity_index_kg_m3_per_mpa: 7.22,
        is_statistically_reliable: false,
        sample_size_status: "VERY_LOW",
      },
    ],
    scope_metadata: {
      plant_code: "PLANT-MUM-01",
      recipe_code: null,
      date_from: null,
      date_to: null,
      cache_token_version: 1,
      generated_at: "2026-09-17T12:00:00Z",
    },
  };

  // 1. Material Summary Cards render correctly
  it("renders material summary cards with exact backend values and units", () => {
    render(<MaterialSummaryCards data={mockMaterialSummary} isLoading={false} />);
    expect(screen.getByText("Produced Batches")).toBeInTheDocument();
    expect(screen.getByText("1,699")).toBeInTheDocument();
    expect(screen.getByText(/4,366/)).toBeInTheDocument();
    expect(screen.getByText("Total Batched Material")).toBeInTheDocument();
    expect(screen.getByText("Total Binder Batched")).toBeInTheDocument();
    expect(screen.getByText("Total Mixing Water")).toBeInTheDocument();
  });

  // 2. Material Summary Cards loading skeleton
  it("renders loading state for MaterialSummaryCards", () => {
    render(<MaterialSummaryCards data={null} isLoading={true} />);
    const loadingItems = screen.getAllByText("Loading material KPI...");
    expect(loadingItems.length).toBe(6);
  });

  // 3. Material Consumption Matrix renders and handles search
  it("renders material consumption matrix table and filters by search", () => {
    render(<MaterialConsumptionMatrix data={mockMaterialSummary} isLoading={false} />);
    expect(screen.getByText("Material Consumption & Specific Density Matrix")).toBeInTheDocument();
    expect(screen.getByText("OPC 53 Grade Cement")).toBeInTheDocument();
    expect(screen.getByText("CEMENT_OPC")).toBeInTheDocument();
    expect(screen.getByText("321.8")).toBeInTheDocument();

    // Search filter test
    const searchInput = screen.getByPlaceholderText("Search material...");
    fireEvent.change(searchInput, { target: { value: "GGBS" } });
    expect(screen.getByText("Ground Granulated Blast-Furnace Slag")).toBeInTheDocument();
    expect(screen.queryByText("OPC 53 Grade Cement")).not.toBeInTheDocument();
  });

  // 4. Annex E Batch Weighing Variance renders exact terminology
  it("renders IS 4926:2003 Annex E Weighment Tolerance Indicator and categories", () => {
    render(<BatchWeighingVarianceChart data={mockBatchVariance} isLoading={false} />);
    expect(screen.getByText("IS 4926:2003 Annex E Weighment Tolerance Indicator")).toBeInTheDocument();
    expect(screen.getByText(/93\.[34]%/)).toBeInTheDocument();
    expect(screen.getByText("Cement & Binders")).toBeInTheDocument();
    expect(screen.getByText(/Tolerance:\s*±2%/)).toBeInTheDocument();
  });

  // 5. Unknown Material handling in Annex E (Not Classifiable)
  it("treats unknown materials as Not Classifiable and displays unclassified notice", () => {
    render(<BatchWeighingVarianceChart data={mockBatchVariance} isLoading={false} />);
    const notClassifiableBadges = screen.getAllByText("Not Classifiable");
    expect(notClassifiableBadges.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/UNKNOWN_FIBER_X/)).toBeInTheDocument();
  });

  // 6. Water & W/B Ratio Chart renders with LIMITED moisture status
  it("renders Water and W/B Ratio monitoring with LIMITED moisture status disclosure", () => {
    render(
      <WaterCementRatioChart
        varianceData={mockBatchVariance}
        efficiencyData={mockBinderEfficiency}
        isLoading={false}
      />
    );
    expect(screen.getByText("Water & Water-to-Binder (W/B) Ratio Monitoring")).toBeInTheDocument();
    expect(screen.getByText("0.395")).toBeInTheDocument();
    expect(screen.getByText("0.528")).toBeInTheDocument();
    expect(screen.getByText(/Moisture Telemetry: LIMITED/i)).toBeInTheDocument();
    expect(screen.getByText(/Raw water variance reflects scale delivery/i)).toBeInTheDocument();
  });

  // 7. Binder Intensity Matrix renders recipe metrics and fleet benchmark
  it("renders Binder Intensity Matrix with fleet benchmark and sample size badges", () => {
    render(<BinderIntensityMatrix data={mockBinderEfficiency} isLoading={false} />);
    expect(screen.getByText("Binder Intensity & Material Efficiency Matrix")).toBeInTheDocument();
    expect(screen.getByText(/9.89 kg\/m³\/MPa/i)).toBeInTheDocument();
    expect(screen.getByText("M-30")).toBeInTheDocument();
    expect(screen.getByText(/9.38/)).toBeInTheDocument();
    expect(screen.getByText(/Reliable/i)).toBeInTheDocument();
    expect(screen.getByText(/Very Low/i)).toBeInTheDocument();
  });

  // 8. Pagination for MixPerformanceMatrix (Phase 2 enhancement)
  it("renders paginated MixPerformanceMatrix with page size and navigation controls", () => {
    const multiItemMix: MixPerformanceListDTO = {
      items: Array.from({ length: 12 }, (_, i) => ({
        recipe_code: `REC-${i + 1}`,
        recipe_name: `Recipe Name ${i + 1}`,
        grade: `M-${20 + i * 5}`,
        target_strength_fck: 20 + i * 5,
        target_mean_strength_fck_prime: 28 + i * 5,
        total_batches: 50,
        tested_batches_28d: 40,
        tested_specimens_28d: 45,
        mean_strength_mpa: 32.0 + i,
        standard_deviation_mpa: 2.5,
        coefficient_of_variation_pct: 7.8,
        strength_margin_mpa: 4.0,
        compliance_rate_pct: 98.0,
        stability_status: "EXCELLENT",
      })),
      total_recipes_evaluated: 12,
      scope_metadata: {
        plant_code: null,
        recipe_code: null,
        date_from: null,
        date_to: null,
        cache_token_version: 1,
        generated_at: "2026-09-17T12:00:00Z",
      },
    };

    render(<MixPerformanceMatrix data={multiItemMix} isLoading={false} />);
    expect(screen.getByText(/Showing/i)).toHaveTextContent(/Showing 1 to 10 of 12 mix designs/i);
    expect(screen.getByText("1 / 2")).toBeInTheDocument();

    // Click Next page
    const nextBtn = screen.getByRole("button", { name: /next/i });
    fireEvent.click(nextBtn);
    expect(screen.getByText(/Showing/i)).toHaveTextContent(/Showing 11 to 12 of 12 mix designs/i);
    expect(screen.getByText("2 / 2")).toBeInTheDocument();
  });

  // 9. Empty States handling
  it("renders honest empty states when no data is provided", () => {
    render(<MaterialConsumptionMatrix data={null} isLoading={false} />);
    expect(screen.getByText("No material consumption records found for selected scope")).toBeInTheDocument();

    render(<BatchWeighingVarianceChart data={null} isLoading={false} />);
    expect(screen.getByText("No batch weighment records available")).toBeInTheDocument();

    render(<BinderIntensityMatrix data={null} isLoading={false} />);
    expect(screen.getByText("No binder efficiency records found for selected scope")).toBeInTheDocument();
  });
});
