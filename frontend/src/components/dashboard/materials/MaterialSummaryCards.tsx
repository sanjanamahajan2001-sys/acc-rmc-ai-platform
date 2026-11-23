import React from "react";
import { enterpriseLightTokens as tokens } from "../../manual-entry/enterpriseLightTokens";
import { MaterialConsumptionSummaryDTO } from "../../../services/reportingService";
import {
  BatchMixerIcon,
  MixerTruckIcon,
  WeighbridgeScaleIcon,
  SiloCementIcon,
  WaterFlowIcon,
  AggregateHopperIcon,
} from "../../icons";

interface MaterialSummaryCardsProps {
  data: MaterialConsumptionSummaryDTO | null;
  isLoading: boolean;
}

export const MaterialSummaryCards: React.FC<MaterialSummaryCardsProps> = ({
  data,
  isLoading,
}) => {
  if (isLoading) {
    return (
      <div className="dashboard-materials-summary-grid">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div
            key={i}
            style={{
              padding: "16px 18px",
              backgroundColor: "#FFFFFF",
              borderRadius: "10px",
              border: `1px solid ${tokens.borderLight}`,
              height: "90px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <span style={{ fontSize: "0.78rem", color: tokens.textMuted }}>Loading material KPI...</span>
          </div>
        ))}
      </div>
    );
  }

  const producedBatches = data?.total_produced_batches ?? data?.total_batches ?? 0;
  const scheduledBatches = data?.total_scheduled_batches ?? 0;
  const totalVolume = data?.total_volume_m3 ?? 0;
  const totalActualMat = data?.total_actual_material_kg ?? 0;
  const totalPlannedMat = data?.total_planned_material_kg ?? 0;
  const totalVarianceKg = data?.total_variance_kg ?? 0;
  const variancePct = data?.overall_variance_percentage ?? 0;
  const totalBinder = data?.total_binder_consumption_kg ?? 0;
  const totalWater = data?.total_water_consumption_kg ?? 0;
  const totalAggregates = data?.total_aggregate_consumption_kg ?? 0;
  const totalAdmixtures = data?.total_admixture_consumption_kg ?? 0;

  const cards = [
    {
      title: "Produced Batches",
      value: producedBatches.toLocaleString(),
      subtext: scheduledBatches > 0 ? `+ ${scheduledBatches} scheduled/planned` : "Batches with scale telemetry",
      icon: <BatchMixerIcon size={18} />,
      badge: "Completed",
      badgeBg: tokens.primaryAccentLight,
      badgeColor: tokens.primaryAccent,
    },
    {
      title: "Produced Volume",
      value: `${totalVolume.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 2 })} m³`,
      subtext: producedBatches > 0 ? `Avg ${(totalVolume / producedBatches).toFixed(1)} m³/batch` : "No production volume",
      icon: <MixerTruckIcon size={18} />,
      badge: "Physical Output",
      badgeBg: "rgba(13, 148, 136, 0.08)",
      badgeColor: "#0D9488",
    },
    {
      title: "Total Batched Material",
      value: `${(totalActualMat / 1000).toFixed(1)} t`,
      subtext: `${totalActualMat.toLocaleString()} kg (${variancePct >= 0 ? "+" : ""}${variancePct.toFixed(2)}% vs plan)`,
      icon: <WeighbridgeScaleIcon size={18} />,
      badge: `${(totalVarianceKg >= 0 ? "+" : "") + totalVarianceKg.toFixed(0)} kg`,
      badgeBg: Math.abs(variancePct) <= 2.0 ? tokens.statusSuccessBg : tokens.statusWarningBg,
      badgeColor: Math.abs(variancePct) <= 2.0 ? tokens.statusSuccessText : tokens.statusWarningText,
    },
    {
      title: "Total Binder Batched",
      value: `${(totalBinder / 1000).toFixed(1)} t`,
      subtext: totalVolume > 0 ? `${(totalBinder / totalVolume).toFixed(1)} kg/m³ density` : `${totalBinder.toLocaleString()} kg`,
      icon: <SiloCementIcon size={18} />,
      badge: "Cement + Minerals",
      badgeBg: tokens.infoBlueLight,
      badgeColor: tokens.infoBlue,
    },
    {
      title: "Total Mixing Water",
      value: `${totalWater.toLocaleString()} kg`,
      subtext: totalVolume > 0 ? `${(totalWater / totalVolume).toFixed(1)} kg/m³ delivered` : "Raw batch scale delivery",
      icon: <WaterFlowIcon size={18} />,
      badge: "Scale Delivery",
      badgeBg: "rgba(2, 132, 199, 0.08)",
      badgeColor: "#0284C7",
    },
    {
      title: "Aggregates & Admixtures",
      value: `${(totalAggregates / 1000).toFixed(1)} t / ${(totalAdmixtures).toFixed(1)} kg`,
      subtext: "Coarse/Fine sand & chemical admixtures",
      icon: <AggregateHopperIcon size={18} />,
      badge: "Agg & SP",
      badgeBg: "rgba(124, 58, 237, 0.08)",
      badgeColor: "#7C3AED",
    },
  ];

  return (
    <div className="dashboard-materials-summary-grid">
      {cards.map((card, idx) => (
        <div
          key={idx}
          style={{
            padding: "14px 18px",
            backgroundColor: "#FFFFFF",
            borderRadius: "10px",
            border: `1px solid ${tokens.borderLight}`,
            boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.02)",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            boxSizing: "border-box",
            minWidth: 0,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div
                style={{
                  padding: "6px",
                  borderRadius: "6px",
                  backgroundColor: "#F8FAFC",
                  border: `1px solid ${tokens.borderLight}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                {card.icon}
              </div>
              <span style={{ fontSize: "0.75rem", fontWeight: 600, color: tokens.textSecondary }}>
                {card.title}
              </span>
            </div>
            <span
              style={{
                fontSize: "0.65rem",
                fontWeight: 600,
                padding: "2px 6px",
                borderRadius: "4px",
                backgroundColor: card.badgeBg,
                color: card.badgeColor,
                whiteSpace: "nowrap",
              }}
            >
              {card.badge}
            </span>
          </div>

          <div>
            <div
              style={{
                fontSize: "1.25rem",
                fontWeight: 700,
                color: tokens.textPrimary,
                lineHeight: 1.2,
                letterSpacing: "-0.01em",
              }}
            >
              {card.value}
            </div>
            <div
              style={{
                fontSize: "0.72rem",
                color: tokens.textMuted,
                marginTop: "3px",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
              title={card.subtext}
            >
              {card.subtext}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
