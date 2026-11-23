import React from "react";
import { Activity, RefreshCw, Wifi, WifiOff } from "lucide-react";
import { SyncStatus } from "../../hooks/useDashboardEventStream";
import { enterpriseLightTokens as tokens } from "../manual-entry/enterpriseLightTokens";

interface LiveSyncIndicatorProps {
  status: SyncStatus;
}

export const LiveSyncIndicator: React.FC<LiveSyncIndicatorProps> = ({ status }) => {
  let badgeBg = tokens.statusSuccessBg;
  let badgeBorder = tokens.statusSuccessBorder;
  let badgeText = tokens.statusSuccessText;
  let label = "Live (Event-Driven)";
  let icon = <Wifi size={13} />;

  if (status === "SYNCING") {
    badgeBg = tokens.statusWarningBg;
    badgeBorder = tokens.statusWarningBorder;
    badgeText = tokens.statusWarningText;
    label = "Syncing Update...";
    icon = <RefreshCw size={13} className="animate-spin" />;
  } else if (status === "RECONNECTING") {
    badgeBg = "#EFF6FF";
    badgeBorder = "#BFDBFE";
    badgeText = "#1D4ED8";
    label = "Reconnecting...";
    icon = <Activity size={13} className="animate-pulse" />;
  } else if (status === "OFFLINE") {
    badgeBg = tokens.statusErrorBg;
    badgeBorder = tokens.statusErrorBorder;
    badgeText = tokens.statusErrorText;
    label = "Offline (Reconciling)";
    icon = <WifiOff size={13} />;
  }

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        padding: "4px 10px",
        borderRadius: "9999px",
        backgroundColor: badgeBg,
        border: `1px solid ${badgeBorder}`,
        color: badgeText,
        fontSize: "0.72rem",
        fontWeight: 600,
        letterSpacing: "0.02em",
        userSelect: "none",
        transition: "all 0.2s ease-in-out",
      }}
    >
      <span
        style={{
          display: "inline-block",
          width: "6px",
          height: "6px",
          borderRadius: "50%",
          backgroundColor: status === "LIVE" ? "#10B981" : status === "SYNCING" ? "#F59E0B" : "#EF4444",
        }}
      />
      {icon}
      <span>{label}</span>
    </div>
  );
};
