import React, { useState, useEffect, useCallback } from "react";
import { ShieldCheck, RefreshCw, Download, Layers, Database, Users, Shield, CheckCircle2, TestTube, Cpu, Sliders, Sparkles } from "lucide-react";
import { AppShell } from "../components/AppShell";
import { AuditMetricsCards } from "../components/audit/AuditMetricsCards";
import { AuditFilterBar } from "../components/audit/AuditFilterBar";
import { AuditTable } from "../components/audit/AuditTable";
import { AuditDetailDrawer } from "../components/audit/AuditDetailDrawer";
import { AuditCorrelationModal } from "../components/audit/AuditCorrelationModal";
import { auditService } from "../services/auditService";
import { AuditEventItem, AuditMetrics, AuditQueryParams } from "../types/audit";
import { enterpriseLightTokens as tokens, primaryButtonBase, secondaryButtonBase } from "../components/manual-entry/enterpriseLightTokens";

export const AuditGovernancePage: React.FC = () => {
  // Active Domain Tab
  const [activeTab, setActiveTab] = useState<string>("ALL");

  // Query & Filter State
  const [filters, setFilters] = useState<AuditQueryParams>({
    page: 1,
    page_size: 25,
    sort_by: "created_at",
    sort_desc: true,
  });

  // Data State
  const [events, setEvents] = useState<AuditEventItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [metrics, setMetrics] = useState<AuditMetrics | null>(null);

  // UI State
  const [loadingEvents, setLoadingEvents] = useState<boolean>(true);
  const [loadingMetrics, setLoadingMetrics] = useState<boolean>(true);
  const [exporting, setExporting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Detail & Correlation Modals
  const [selectedEvent, setSelectedEvent] = useState<AuditEventItem | null>(null);
  const [selectedCorrelationId, setSelectedCorrelationId] = useState<string | null>(null);

  // Load Metrics
  const loadMetrics = useCallback(async () => {
    try {
      setLoadingMetrics(true);
      const data = await auditService.getMetrics();
      setMetrics(data);
    } catch (err: any) {
      console.error("Failed to load audit metrics:", err);
    } finally {
      setLoadingMetrics(false);
    }
  }, []);

  // Load Events
  const loadEvents = useCallback(async () => {
    try {
      setLoadingEvents(true);
      setError(null);
      
      const queryParams: AuditQueryParams = {
        ...filters,
        module: activeTab !== "ALL" ? activeTab : filters.module,
      };

      const res = await auditService.getEvents(queryParams);
      setEvents(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err: any) {
      console.error("Failed to load audit events:", err);
      setError(err.message || "Failed to load audit events from server.");
    } finally {
      setLoadingEvents(false);
    }
  }, [filters, activeTab]);

  useEffect(() => {
    loadMetrics();
  }, [loadMetrics]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  // Tab change handler
  const handleTabChange = (tabKey: string) => {
    setActiveTab(tabKey);
    setFilters((prev) => ({
      ...prev,
      page: 1,
      module: tabKey !== "ALL" ? tabKey : undefined,
    }));
  };

  const handleFilterChange = (newFilters: Partial<AuditQueryParams>) => {
    if ("module" in newFilters) {
      setActiveTab(newFilters.module || "ALL");
    }
    setFilters((prev) => ({
      ...prev,
      ...newFilters,
    }));
  };

  const handleResetFilters = () => {
    setActiveTab("ALL");
    setFilters({
      page: 1,
      page_size: 25,
      sort_by: "created_at",
      sort_desc: true,
      module: undefined,
    });
  };

  const handleExport = async () => {
    try {
      setExporting(true);
      const queryParams: AuditQueryParams = {
        ...filters,
        module: activeTab !== "ALL" ? activeTab : filters.module,
      };
      const exportUrl = auditService.getExportUrl(queryParams);
      window.open(exportUrl, "_blank");
    } catch (err) {
      console.error("Failed to initiate audit export:", err);
    } finally {
      setExporting(false);
    }
  };

  const tabs = [
    { key: "ALL", label: "All Events", icon: ShieldCheck },
    { key: "AUTH", label: "Authentication", icon: Shield },
    { key: "USER_ADMIN", label: "User Management", icon: Users },
    { key: "DATA_INGESTION", label: "Data Ingestion", icon: Database },
    { key: "MANUAL_ENTRY", label: "Manual Entry", icon: Layers },
    { key: "MODEL_TRAINING", label: "Model Training", icon: Cpu },
    { key: "AI_MIX_OPTIMIZATION", label: "Mix Optimization", icon: Sparkles },
    { key: "SETTINGS", label: "Settings & Calibre", icon: Sliders },
    // { key: "QUALITY_QA", label: "Quality & QA", icon: TestTube },
    // { key: "MASTER_DATA", label: "Master Data", icon: CheckCircle2 },
    // { key: "SECURITY", label: "Security & RBAC", icon: ShieldCheck },
  ];

  return (
    <AppShell>
      <main className="page-main-container" style={{ padding: "20px 24px", minWidth: 0, width: "100%" }}>
        {/* Breadcrumb & Header */}
        <div style={{ marginBottom: "20px" }}>
          <div style={{ fontSize: "0.75rem", color: tokens.textMuted, marginBottom: "6px" }}>
            ACC Platform / Administration / <span style={{ color: tokens.primaryAccent, fontWeight: 600 }}>Audit & Governance</span>
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
            <div>
              <h1 style={{ fontSize: "1.3rem", fontWeight: 800, margin: 0, color: tokens.textPrimary, letterSpacing: "-0.02em" }}>
                🛡️ Audit & Governance Center
              </h1>
              <p style={{ fontSize: "0.82rem", color: tokens.textMuted, margin: "3px 0 0 0" }}>
                Centralized enterprise accountability, operational lineage, and security compliance ledger
              </p>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <button
                type="button"
                onClick={() => {
                  loadMetrics();
                  loadEvents();
                }}
                disabled={loadingEvents}
                aria-label="Refresh audit data"
                style={{
                  ...secondaryButtonBase,
                  minHeight: "38px",
                  padding: "8px 14px",
                  fontSize: "0.8rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <RefreshCw size={14} className={loadingEvents ? "animate-spin" : ""} />
                <span>Refresh</span>
              </button>


            </div>
          </div>
        </div>

        {/* Error Notification */}
        {error && (
          <div
            style={{
              padding: "12px 16px",
              backgroundColor: "#FEE2E2",
              border: "1px solid #FCA5A5",
              borderRadius: "8px",
              color: "#991B1B",
              fontSize: "0.82rem",
              marginBottom: "16px",
            }}
          >
            {error}
          </div>
        )}

        {/* Domain Navigation Tabs */}
        <div data-tour="audit-domain-tabs"
          style={{
            display: "flex",
            gap: "6px",
            overflowX: "auto",
            paddingBottom: "8px",
            marginBottom: "16px",
            borderBottom: `1px solid ${tokens.border}`,
          }}
        >
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => handleTabChange(tab.key)}
                aria-label={`View ${tab.label} audit events`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "8px 14px",
                  borderRadius: "6px",
                  fontSize: "0.8rem",
                  fontWeight: active ? 700 : 500,
                  color: active ? tokens.primaryAccent : tokens.textSecondary,
                  backgroundColor: active ? tokens.primaryAccentLight : "transparent",
                  border: active ? `1px solid ${tokens.primaryAccentBorder}` : "1px solid transparent",
                  cursor: "pointer",
                  whiteSpace: "nowrap",
                  transition: "all 0.15s ease",
                }}
              >
                <Icon size={14} color={active ? tokens.primaryAccent : "#64748B"} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Live Aggregated Metrics Cards */}
        <div data-tour="audit-metrics-cards">
          <AuditMetricsCards metrics={metrics} loading={loadingMetrics} />
        </div>

        <div data-tour="audit-table-section">
        {/* Dynamic Search & Multi-Filter Bar */}
        <AuditFilterBar
          filters={filters}
          onFilterChange={handleFilterChange}
          onResetFilters={handleResetFilters}
          onExport={handleExport}
          exporting={exporting}
        />

        {/* Paginated Audit Events Table */}
        <AuditTable
          events={events}
          loading={loadingEvents}
          total={total}
          page={filters.page || 1}
          pageSize={filters.page_size || 25}
          totalPages={totalPages}
          onPageChange={(p) => handleFilterChange({ page: p })}
          onPageSizeChange={(ps) => handleFilterChange({ page_size: ps, page: 1 })}
          onSelectEvent={(ev) => setSelectedEvent(ev)}
          onSelectCorrelation={(cid) => setSelectedCorrelationId(cid)}
        />

        </div>

        {/* Single Event Detail Inspector Drawer */}
        <AuditDetailDrawer
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
          onViewCorrelation={(cid) => {
            setSelectedEvent(null);
            setSelectedCorrelationId(cid);
          }}
        />

        {/* End-to-End Correlation Timeline Trace Modal */}
        <AuditCorrelationModal
          correlationId={selectedCorrelationId}
          onClose={() => setSelectedCorrelationId(null)}
          onSelectEvent={(ev) => {
            setSelectedCorrelationId(null);
            setSelectedEvent(ev);
          }}
        />
      </main>
    </AppShell>
  );
};

export default AuditGovernancePage;
