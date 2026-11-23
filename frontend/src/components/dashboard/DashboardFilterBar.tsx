import React from "react";
import { Filter, Calendar, Building2, FlaskConical, RotateCcw } from "lucide-react";
import { enterpriseLightTokens as tokens } from "../manual-entry/enterpriseLightTokens";
import { FilterOptionsDTO } from "../../services/reportingService";

interface DashboardFilterBarProps {
  filterOptions: FilterOptionsDTO | null;
  selectedPlant: string;
  selectedRecipe: string;
  dateFrom: string;
  dateTo: string;
  onPlantChange: (plantCode: string) => void;
  onRecipeChange: (recipeCode: string) => void;
  onDateFromChange: (date: string) => void;
  onDateToChange: (date: string) => void;
  onResetFilters: () => void;
  isLoading?: boolean;
}

export const DashboardFilterBar: React.FC<DashboardFilterBarProps> = ({
  filterOptions,
  selectedPlant,
  selectedRecipe,
  dateFrom,
  dateTo,
  onPlantChange,
  onRecipeChange,
  onDateFromChange,
  onDateToChange,
  onResetFilters,
  isLoading = false,
}) => {
  const hasActiveFilters = Boolean(selectedPlant || selectedRecipe || dateFrom || dateTo);

  return (
    <div className="dashboard-filter-bar-container">
      <div className="dashboard-filter-group">
        {/* Plant Selector */}
        <div className="dashboard-filter-item">
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Building2 size={16} color={tokens.textMuted} />
            <span style={{ fontSize: "0.82rem", fontWeight: 600, color: tokens.textSecondary }}>
              Plant Scope:
            </span>
          </div>
          <select
            value={selectedPlant}
            onChange={(e) => onPlantChange(e.target.value)}
            disabled={isLoading}
            className="dashboard-filter-select"
          >
            <option value="">All Production Plants</option>
            {filterOptions?.plants.map((p) => (
              <option key={p.plant_code} value={p.plant_code}>
                {p.plant_code} — {p.plant_name}
              </option>
            ))}
          </select>
        </div>

        {/* Recipe / Grade Selector */}
        <div className="dashboard-filter-item">
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <FlaskConical size={16} color={tokens.textMuted} />
            <span style={{ fontSize: "0.82rem", fontWeight: 600, color: tokens.textSecondary }}>
              Mix Design:
            </span>
          </div>
          <select
            value={selectedRecipe}
            onChange={(e) => onRecipeChange(e.target.value)}
            disabled={isLoading}
            className="dashboard-filter-select"
          >
            <option value="">All Mix Grades</option>
            {filterOptions?.recipes.map((r) => (
              <option key={r.recipe_code} value={r.recipe_code}>
                {r.grade ? `[${r.grade}] ` : ""}{r.recipe_code} — {r.recipe_name}
              </option>
            ))}
          </select>
        </div>

        {/* Date Range Selectors */}
        <div className="dashboard-filter-item">
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <Calendar size={16} color={tokens.textMuted} />
            <span style={{ fontSize: "0.82rem", fontWeight: 600, color: tokens.textSecondary }}>
              Production Date:
            </span>
          </div>
          <div className="dashboard-date-range-box">
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => onDateFromChange(e.target.value)}
              disabled={isLoading}
              style={{
                padding: "5px 8px",
                fontSize: "0.8rem",
                borderRadius: "6px",
                border: `1px solid ${tokens.border}`,
                backgroundColor: tokens.surfacePrimary,
                color: tokens.textPrimary,
                outline: "none",
                width: "100%",
                boxSizing: "border-box",
              }}
            />
            <span style={{ fontSize: "0.78rem", color: tokens.textMuted, textAlign: "center" }}>to</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => onDateToChange(e.target.value)}
              disabled={isLoading}
              style={{
                padding: "5px 8px",
                fontSize: "0.8rem",
                borderRadius: "6px",
                border: `1px solid ${tokens.border}`,
                backgroundColor: tokens.surfacePrimary,
                color: tokens.textPrimary,
                outline: "none",
                width: "100%",
                boxSizing: "border-box",
              }}
            />
          </div>
        </div>
      </div>

      {/* Reset Filter Action */}
      {hasActiveFilters && (
        <button
          type="button"
          onClick={onResetFilters}
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "6px",
            padding: "6px 14px",
            fontSize: "0.78rem",
            fontWeight: 600,
            color: tokens.primaryAccent,
            backgroundColor: tokens.surfaceSecondary,
            border: `1px solid ${tokens.border}`,
            borderRadius: "6px",
            cursor: "pointer",
            alignSelf: "flex-end",
          }}
        >
          <RotateCcw size={13} />
          <span>Reset Filters</span>
        </button>
      )}
    </div>
  );
};
