import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import {
  ParetoFrontierChart,
  OptimizationCandidateDTO,
  BaselineRecipeCoordinatesDTO,
} from "../components/dashboard/optimization/ParetoFrontierChart";

const mockBaseline: BaselineRecipeCoordinatesDTO = {
  recipe_code: "REC-M30-STANDARD",
  grade: "M-30",
  characteristic_strength_fck_mpa: 30.0,
  target_mean_strength_fck_prime_mpa: 38.25,
  predicted_strength_mpa: 40.5,
  binder_intensity_kg_m3: 380.0,
  cost_per_m3: null,
  water_binder_ratio: 0.46,
};

const mockCandidates: OptimizationCandidateDTO[] = [
  {
    id: "cand-1",
    candidate_identifier: "CAND-01",
    predicted_strength_mpa: 41.2,
    target_mean_strength_mpa: 38.25,
    characteristic_strength_fck_mpa: 30.0,
    strength_margin_mpa: 2.95,
    strength_gate_status: "PASSED",
    prediction_source: "ML_MODEL",
    prediction_source_semantics: "Analytical Prediction — Limited Validation",
    model_name: "acc_concrete_28d_strength",
    model_version: "1.0.0",
    binder_intensity_kg_m3: 350.0,
    cost_per_m3: null,
    water_binder_ratio: 0.44,
    water_cement_ratio: 0.55,
    is_feasible: true,
    is_non_dominated: true,
    is_recommended: null,
    physical_volume_diagnostic: {
      volume_balance_actual_m3: 1.001,
      volume_balance_target_m3: 1.000,
      volume_balance_deviation_m3: 0.001,
      volume_tolerance_limit_m3: 0.010,
      air_volume_m3: 0.010,
      validation_status: "PASSED",
    },
    constraint_diagnostics: [
      {
        constraint_name: "Minimum Total Binder Content",
        standard_reference: "IS 456:2000 Table 5 (Moderate)",
        limit_value: 300.0,
        actual_value: 350.0,
        unit: "kg/m³",
        comparison: "MINIMUM",
        status: "PASSED",
        margin: 50.0,
      },
    ],
    constituents: [
      {
        material_code: "CEM-OPC",
        material_name: "OPC 53 Grade",
        category_code: "CEMENT",
        quantity_kg_m3: 280.0,
        specific_gravity: 3.15,
        absolute_volume_m3: 0.0889,
      },
    ],
  },
  {
    id: "cand-2",
    candidate_identifier: "CAND-02",
    predicted_strength_mpa: 37.0,
    target_mean_strength_mpa: 38.25,
    characteristic_strength_fck_mpa: 30.0,
    strength_margin_mpa: -1.25,
    strength_gate_status: "FAILED",
    prediction_source: "ML_MODEL",
    prediction_source_semantics: "Analytical Prediction — Limited Validation",
    model_name: "acc_concrete_28d_strength",
    model_version: "1.0.0",
    binder_intensity_kg_m3: 320.0,
    cost_per_m3: null,
    water_binder_ratio: 0.48,
    water_cement_ratio: 0.60,
    is_feasible: false,
    is_non_dominated: false,
    is_recommended: null,
    physical_volume_diagnostic: {
      volume_balance_actual_m3: 1.002,
      volume_balance_target_m3: 1.000,
      volume_balance_deviation_m3: 0.002,
      volume_tolerance_limit_m3: 0.010,
      air_volume_m3: 0.010,
      validation_status: "PASSED",
    },
    constraint_diagnostics: [],
    constituents: [],
  },
];

describe("ParetoFrontierChart Component", () => {
  it("renders Pareto Frontier title, candidate identifiers, and reference lines", () => {
    const onSelect = vi.fn();
    render(
      <ParetoFrontierChart
        candidates={mockCandidates}
        baseline={mockBaseline}
        targetMeanStrength={38.25}
        fck={30.0}
        objective="MINIMIZE_BINDER"
        selectedCandidateId={null}
        onSelectCandidate={onSelect}
      />
    );

    expect(screen.getByText(/Pareto Optimization Frontier/i)).toBeInTheDocument();
    expect(screen.getByText(/Target Mean f'ck = 38.25 MPa/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Master Recipe Baseline/i).length).toBeGreaterThan(0);
    expect(screen.getByText("CAND-01")).toBeInTheDocument();
  });

  it("handles candidate click selection properly", () => {
    const onSelect = vi.fn();
    render(
      <ParetoFrontierChart
        candidates={mockCandidates}
        baseline={mockBaseline}
        targetMeanStrength={38.25}
        fck={30.0}
        objective="MINIMIZE_BINDER"
        selectedCandidateId={null}
        onSelectCandidate={onSelect}
      />
    );

    const cand1Node = screen.getByTestId("candidate-node-CAND-01");
    fireEvent.click(cand1Node);
    expect(onSelect).toHaveBeenCalledWith(mockCandidates[0]);
  });

  it("toggles infeasible candidate visibility when toggle button is clicked", () => {
    const onSelect = vi.fn();
    render(
      <ParetoFrontierChart
        candidates={mockCandidates}
        baseline={mockBaseline}
        targetMeanStrength={38.25}
        fck={30.0}
        objective="MINIMIZE_BINDER"
        selectedCandidateId={null}
        onSelectCandidate={onSelect}
      />
    );

    const toggleBtn = screen.getByRole("button", { name: /Hide Infeasible/i });
    expect(toggleBtn).toBeInTheDocument();
    fireEvent.click(toggleBtn);
    expect(screen.getByRole("button", { name: /Show Infeasible/i })).toBeInTheDocument();
  });
});
