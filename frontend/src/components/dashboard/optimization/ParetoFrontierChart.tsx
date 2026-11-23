import React, { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { TargetAccuracyIcon } from "../../icons";

export interface CandidateConstituentDTO {
  material_code: string;
  material_name: string;
  category_code: string;
  quantity_kg_m3: number;
  specific_gravity: number;
  absolute_volume_m3: number;
}

export interface ConstraintDiagnosticItemDTO {
  constraint_name: string;
  standard_reference: string;
  limit_value: number;
  actual_value: number;
  unit: string;
  comparison: string;
  status: string;
  margin: number;
}

export interface PhysicalVolumeDiagnosticDTO {
  volume_balance_actual_m3: number;
  volume_balance_target_m3: number;
  volume_balance_deviation_m3: number;
  volume_tolerance_limit_m3: number;
  air_volume_m3: number;
  validation_status: string;
}

export interface OptimizationCandidateDTO {
  id: string;
  candidate_identifier: string;
  predicted_strength_mpa: number;
  target_mean_strength_mpa: number;
  characteristic_strength_fck_mpa: number;
  strength_margin_mpa: number;
  strength_gate_status: string;
  prediction_source: string;
  prediction_source_semantics: string;
  model_name: string;
  model_version: string;
  binder_intensity_kg_m3: number;
  cost_per_m3: number | null;
  water_binder_ratio: number;
  water_cement_ratio: number;
  is_feasible: boolean;
  is_non_dominated: boolean;
  is_recommended: boolean | null;
  physical_volume_diagnostic: PhysicalVolumeDiagnosticDTO;
  constraint_diagnostics: ConstraintDiagnosticItemDTO[];
  constituents: CandidateConstituentDTO[];
}

export interface BaselineRecipeCoordinatesDTO {
  recipe_code: string;
  grade: string;
  characteristic_strength_fck_mpa: number;
  target_mean_strength_fck_prime_mpa: number;
  predicted_strength_mpa: number;
  binder_intensity_kg_m3: number;
  cost_per_m3: number | null;
  water_binder_ratio: number;
}

interface ParetoFrontierChartProps {
  candidates: OptimizationCandidateDTO[];
  baseline: BaselineRecipeCoordinatesDTO;
  targetMeanStrength: number;
  fck: number;
  objective: string;
  selectedCandidateId: string | null;
  onSelectCandidate: (candidate: OptimizationCandidateDTO) => void;
}

export const ParetoFrontierChart: React.FC<ParetoFrontierChartProps> = ({
  candidates,
  baseline,
  targetMeanStrength,
  fck,
  objective,
  selectedCandidateId,
  onSelectCandidate,
}) => {
  const [hoveredCandidate, setHoveredCandidate] = useState<OptimizationCandidateDTO | null>(null);
  const [showInfeasible, setShowInfeasible] = useState<boolean>(true);

  // Determine X-axis metric
  const isCost = objective === "MINIMIZE_COST" && candidates.some((c) => c.cost_per_m3 !== null);
  const getX = (c: OptimizationCandidateDTO | BaselineRecipeCoordinatesDTO) => {
    if (isCost && "cost_per_m3" in c && c.cost_per_m3 !== null) {
      return c.cost_per_m3;
    }
    return c.binder_intensity_kg_m3;
  };

  const xLabel = isCost ? "Material Cost (₹/m³)" : "Binder Intensity (kg/m³)";
  const yLabel = "Predicted 28-Day Strength (MPa)";

  // Filter candidates for display
  const displayCandidates = candidates.filter((c) => showInfeasible || c.is_feasible);

  // Compute Bounds with strict NaN protection
  const validX = [...candidates.map(getX), getX(baseline)].filter((v) => typeof v === "number" && !isNaN(v));
  const validY = [
    ...candidates.map((c) => c.predicted_strength_mpa),
    baseline?.predicted_strength_mpa,
    targetMeanStrength,
    fck,
  ].filter((v) => typeof v === "number" && !isNaN(v));

  const minXRaw = validX.length > 0 ? Math.min(...validX) : 250;
  const maxXRaw = validX.length > 0 ? Math.max(...validX) : 550;
  const minYRaw = validY.length > 0 ? Math.min(...validY) : 15;
  const maxYRaw = validY.length > 0 ? Math.max(...validY) : 55;

  const spanX = Math.max(1, maxXRaw - minXRaw);
  const spanY = Math.max(1, maxYRaw - minYRaw);
  const paddingX = Math.max(15, spanX * 0.12);
  const paddingY = Math.max(4, spanY * 0.15);

  const minX = Math.max(0, minXRaw - paddingX);
  const maxX = maxXRaw + paddingX;
  const minY = Math.max(0, minYRaw - paddingY);
  const maxY = maxYRaw + paddingY;

  // Compact, balanced chart dimensions
  const svgWidth = 840;
  const svgHeight = 280;
  const margin = { top: 28, right: 30, bottom: 40, left: 52 };
  const plotWidth = svgWidth - margin.left - margin.right;
  const plotHeight = svgHeight - margin.top - margin.bottom;

  const scaleX = (val: number) => {
    if (typeof val !== "number" || isNaN(val)) return margin.left;
    return margin.left + ((val - minX) / (maxX - minX || 1)) * plotWidth;
  };
  const scaleY = (val: number) => {
    if (typeof val !== "number" || isNaN(val)) return margin.top + plotHeight;
    return margin.top + plotHeight - ((val - minY) / (maxY - minY || 1)) * plotHeight;
  };

  // Sort Pareto candidates by X ascending to draw the frontier curve
  const paretoPoints = candidates
    .filter(
      (c) =>
        c.is_feasible &&
        c.is_non_dominated &&
        typeof getX(c) === "number" &&
        !isNaN(getX(c)) &&
        typeof c.predicted_strength_mpa === "number" &&
        !isNaN(c.predicted_strength_mpa)
    )
    .sort((a, b) => getX(a) - getX(b));

  const paretoPathD =
    paretoPoints.length > 0
      ? paretoPoints
          .map((p, idx) => {
            const x = scaleX(getX(p));
            const y = scaleY(p.predicted_strength_mpa);
            if (isNaN(x) || isNaN(y)) return null;
            return `${idx === 0 ? "M" : "L"} ${x} ${y}`;
          })
          .filter(Boolean)
          .join(" ")
      : "";

  return (
    <div
      style={{
        backgroundColor: "#FFFFFF",
        border: "1px solid #E2E8F0",
        borderRadius: "10px",
        padding: "clamp(10px, 2vw, 16px)",
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        boxShadow: "0 1px 3px rgba(0, 0, 0, 0.04)",
      }}
    >
      {/* Header & Controls */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <TargetAccuracyIcon size={18} />
          <h4 style={{ margin: 0, fontSize: "0.86rem", fontWeight: 700, color: "#0F172A" }}>
            Pareto Optimization Frontier ({xLabel} vs. {yLabel})
          </h4>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <button
            type="button"
            onClick={() => setShowInfeasible(!showInfeasible)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
              padding: "3px 8px",
              fontSize: "0.72rem",
              fontWeight: 600,
              backgroundColor: showInfeasible ? "#F1F5F9" : "#E2E8F0",
              color: "#475569",
              border: "1px solid #CBD5E1",
              borderRadius: "5px",
              cursor: "pointer",
            }}
          >
            {showInfeasible ? <EyeOff size={13} /> : <Eye size={13} />}
            <span>{showInfeasible ? "Hide Infeasible" : "Show Infeasible"}</span>
          </button>

          <span
            style={{
              fontSize: "0.72rem",
              fontWeight: 700,
              color: "#059669",
              backgroundColor: "#ECFDF5",
              padding: "2px 7px",
              borderRadius: "4px",
              border: "1px solid #A7F3D0",
            }}
          >
            {paretoPoints.length} Pareto Optimal Solution{paretoPoints.length === 1 ? "" : "s"}
          </span>
        </div>
      </div>

      {/* SVG Scatter Plot Canvas */}
      <div style={{ position: "relative", width: "100%", overflow: "hidden" }}>
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{ width: "100%", height: "auto", maxHeight: "280px", display: "block" }}
        >
          {/* Background grid lines */}
          {[0.25, 0.5, 0.75, 1.0].map((ratio) => {
            const yVal = minY + (maxY - minY) * ratio;
            const y = scaleY(yVal);
            return (
              <g key={`grid-y-${ratio}`}>
                <line
                  x1={margin.left}
                  y1={y}
                  x2={margin.left + plotWidth}
                  y2={y}
                  stroke="#F1F5F9"
                  strokeWidth="1"
                  strokeDasharray="4 4"
                />
                <text
                  x={margin.left - 8}
                  y={y + 3.5}
                  textAnchor="end"
                  fontSize="9.5"
                  fill="#64748B"
                  fontFamily="sans-serif"
                >
                  {yVal.toFixed(1)}
                </text>
              </g>
            );
          })}

          {[0.2, 0.4, 0.6, 0.8].map((ratio) => {
            const xVal = minX + (maxX - minX) * ratio;
            const x = scaleX(xVal);
            return (
              <g key={`grid-x-${ratio}`}>
                <line
                  x1={x}
                  y1={margin.top}
                  x2={x}
                  y2={margin.top + plotHeight}
                  stroke="#F1F5F9"
                  strokeWidth="1"
                  strokeDasharray="4 4"
                />
                <text
                  x={x}
                  y={margin.top + plotHeight + 15}
                  textAnchor="middle"
                  fontSize="9.5"
                  fill="#64748B"
                  fontFamily="sans-serif"
                >
                  {Math.round(xVal)}
                </text>
              </g>
            );
          })}

          {/* Target Mean Strength Horizontal Threshold Line */}
          {targetMeanStrength >= minY && targetMeanStrength <= maxY && (
            <g>
              <line
                x1={margin.left}
                y1={scaleY(targetMeanStrength)}
                x2={margin.left + plotWidth}
                y2={scaleY(targetMeanStrength)}
                stroke="#DC2626"
                strokeWidth="1.5"
                strokeDasharray="5 3"
              />
              <text
                x={margin.left + plotWidth - 6}
                y={scaleY(targetMeanStrength) - 5}
                textAnchor="end"
                fontSize="9.5"
                fontWeight="700"
                fill="#DC2626"
                fontFamily="sans-serif"
              >
                Target Mean f'ck = {targetMeanStrength.toFixed(2)} MPa
              </text>
            </g>
          )}

          {/* Pareto Frontier Step/Line Curve */}
          {paretoPathD && (
            <path
              d={paretoPathD}
              fill="none"
              stroke="#059669"
              strokeWidth="2.2"
              strokeDasharray="none"
              opacity={0.85}
            />
          )}

          {/* Infeasible Candidates (Muted) */}
          {displayCandidates
            .filter((c) => !c.is_feasible)
            .map((c) => {
              const cx = scaleX(getX(c));
              const cy = scaleY(c.predicted_strength_mpa);
              const isSelected = selectedCandidateId === c.id;
              return (
                <circle
                  key={c.id || c.candidate_identifier}
                  data-testid={`candidate-node-${c.candidate_identifier}`}
                  cx={cx}
                  cy={cy}
                  r={isSelected ? 7 : 5}
                  fill="#94A3B8"
                  opacity={0.45}
                  stroke={isSelected ? "#0F172A" : "transparent"}
                  strokeWidth={isSelected ? 2 : 0}
                  style={{ cursor: "pointer", transition: "all 0.15s" }}
                  onMouseEnter={() => setHoveredCandidate(c)}
                  onMouseLeave={() => setHoveredCandidate(null)}
                  onClick={() => onSelectCandidate(c)}
                />
              );
            })}

          {/* Feasible (Dominated) Candidates */}
          {displayCandidates
            .filter((c) => c.is_feasible && !c.is_non_dominated)
            .map((c) => {
              const cx = scaleX(getX(c));
              const cy = scaleY(c.predicted_strength_mpa);
              const isSelected = selectedCandidateId === c.id;
              return (
                <circle
                  key={c.id || c.candidate_identifier}
                  data-testid={`candidate-node-${c.candidate_identifier}`}
                  cx={cx}
                  cy={cy}
                  r={isSelected ? 7.5 : 5.5}
                  fill="#2563EB"
                  stroke={isSelected ? "#0F172A" : "#DBEAFE"}
                  strokeWidth={isSelected ? 2 : 1}
                  style={{ cursor: "pointer", transition: "all 0.15s" }}
                  onMouseEnter={() => setHoveredCandidate(c)}
                  onMouseLeave={() => setHoveredCandidate(null)}
                  onClick={() => onSelectCandidate(c)}
                />
              );
            })}

          {/* Pareto Optimal Candidates */}
          {displayCandidates
            .filter((c) => c.is_feasible && c.is_non_dominated)
            .map((c) => {
              const cx = scaleX(getX(c));
              const cy = scaleY(c.predicted_strength_mpa);
              const isSelected = selectedCandidateId === c.id;
              return (
                <g
                  key={c.id || c.candidate_identifier}
                  data-testid={`candidate-node-${c.candidate_identifier}`}
                  style={{ cursor: "pointer" }}
                  onClick={() => onSelectCandidate(c)}
                >
                  <circle
                    cx={cx}
                    cy={cy}
                    r={isSelected ? 8 : 6.5}
                    fill="#059669"
                    stroke={isSelected ? "#0F172A" : "#D1FAE5"}
                    strokeWidth={isSelected ? 2.5 : 2}
                    onMouseEnter={() => setHoveredCandidate(c)}
                    onMouseLeave={() => setHoveredCandidate(null)}
                  />
                  <text
                    x={cx}
                    y={cy - 9}
                    textAnchor="middle"
                    fontSize="8.5"
                    fontWeight="700"
                    fill="#059669"
                    fontFamily="monospace"
                  >
                    {c.candidate_identifier}
                  </text>
                </g>
              );
            })}

          {/* Baseline Master Recipe Marker */}
          {(() => {
            const bx = scaleX(getX(baseline));
            const by = scaleY(baseline.predicted_strength_mpa);
            const labelY = Math.abs(by - scaleY(targetMeanStrength)) < 25 ? (by > scaleY(targetMeanStrength) ? by + 16 : by - 10) : (by > plotHeight / 2 ? by - 10 : by + 16);
            return (
              <g>
                <rect
                  x={bx - 5}
                  y={by - 5}
                  width="10"
                  height="10"
                  transform={`rotate(45 ${bx} ${by})`}
                  fill="#4F46E5"
                  stroke="#FFFFFF"
                  strokeWidth="2"
                />
                <text
                  x={bx}
                  y={labelY}
                  textAnchor="middle"
                  fontSize="8.5"
                  fontWeight="700"
                  fill="#4F46E5"
                  fontFamily="sans-serif"
                >
                  Master Recipe Baseline
                </text>
              </g>
            );
          })()}

          {/* Axis Titles */}
          <text
            x={margin.left + plotWidth / 2}
            y={svgHeight - 6}
            textAnchor="middle"
            fontSize="10"
            fontWeight="600"
            fill="#475569"
            fontFamily="sans-serif"
          >
            {xLabel}
          </text>

          <text
            x={-(margin.top + plotHeight / 2)}
            y={14}
            transform="rotate(-90)"
            textAnchor="middle"
            fontSize="10"
            fontWeight="600"
            fill="#475569"
            fontFamily="sans-serif"
          >
            {yLabel}
          </text>
        </svg>

        {/* Hover Tooltip Overlay */}
        {hoveredCandidate && (
          <div
            style={{
              position: "absolute",
              top: "10px",
              right: "10px",
              backgroundColor: "rgba(15, 23, 42, 0.95)",
              color: "#FFFFFF",
              padding: "8px 10px",
              borderRadius: "6px",
              fontSize: "0.72rem",
              boxShadow: "0 4px 12px rgba(0,0,0,0.25)",
              pointerEvents: "none",
              zIndex: 10,
              minWidth: "210px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
              <span style={{ fontWeight: 700, color: "#38BDF8" }}>{hoveredCandidate.candidate_identifier}</span>
              <span
                style={{
                  fontWeight: 600,
                  fontSize: "0.65rem",
                  padding: "1px 5px",
                  borderRadius: "3px",
                  backgroundColor: hoveredCandidate.is_feasible ? (hoveredCandidate.is_non_dominated ? "#059669" : "#2563EB") : "#DC2626",
                }}
              >
                {hoveredCandidate.is_feasible ? (hoveredCandidate.is_non_dominated ? "Pareto Optimal" : "Feasible") : "Infeasible"}
              </span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#94A3B8" }}>Predicted Strength:</span>
                <span style={{ fontWeight: 600 }}>{hoveredCandidate.predicted_strength_mpa.toFixed(1)} MPa</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#94A3B8" }}>Strength Margin:</span>
                <span style={{ fontWeight: 600, color: hoveredCandidate.strength_margin_mpa >= 0 ? "#34D399" : "#F87171" }}>
                  {hoveredCandidate.strength_margin_mpa >= 0 ? "+" : ""}{hoveredCandidate.strength_margin_mpa.toFixed(2)} MPa
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#94A3B8" }}>Total Binder:</span>
                <span style={{ fontWeight: 600 }}>{hoveredCandidate.binder_intensity_kg_m3.toFixed(1)} kg/m³</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#94A3B8" }}>W/B Ratio:</span>
                <span style={{ fontWeight: 600 }}>{hoveredCandidate.water_binder_ratio.toFixed(3)}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#94A3B8" }}>Yield Volume:</span>
                <span style={{ fontWeight: 600 }}>{hoveredCandidate.physical_volume_diagnostic.volume_balance_actual_m3.toFixed(3)} m³</span>
              </div>
              <div style={{ fontSize: "0.65rem", color: "#64748B", borderTop: "1px solid #334155", paddingTop: "3px", marginTop: "2px" }}>
                Source: {hoveredCandidate.prediction_source_semantics}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: "14px",
          fontSize: "0.72rem",
          color: "#475569",
          paddingTop: "5px",
          borderTop: "1px solid #F1F5F9",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
          <div style={{ width: "8px", height: "8px", transform: "rotate(45deg)", backgroundColor: "#4F46E5" }} />
          <span>Master Recipe Baseline</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#059669" }} />
          <span style={{ fontWeight: 600, color: "#059669" }}>Pareto Frontier Solution</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
          <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "#2563EB" }} />
          <span>Feasible Alternative</span>
        </div>
        {showInfeasible && (
          <div style={{ display: "flex", alignItems: "center", gap: "5px" }}>
            <div style={{ width: "7px", height: "7px", borderRadius: "50%", backgroundColor: "#94A3B8", opacity: 0.5 }} />
            <span style={{ color: "#94A3B8" }}>Infeasible (Constraint / Strength Violated)</span>
          </div>
        )}
      </div>
    </div>
  );
};
