/**
 * Tour Service & Global Step Definitions for ACC RMC AI Platform.
 * Supports interactive coachmarks walkthrough with automated cross-route navigation.
 */

export type TourCategory =
  | "Platform Overview"
  | "Quality Analytics"
  | "Mix Optimization"
  | "Dataset Ingestion"
  | "Manual Entry"
  | "Governance & Audit"
  | "Platform Administration"
  | "System Settings"
  | "Platform Help";

export interface TourStep {
  id: string;
  targetSelector: string;
  route: string;
  category: TourCategory;
  badge: string;
  title: string;
  content: string;
  placement?: "top" | "bottom" | "left" | "right";
}

export interface CategoryTheme {
  primary: string;
  bgLight: string;
  glow: string;
  tag: string;
}

export const CATEGORY_THEMES: Record<string, CategoryTheme> = {
  "Platform Overview": {
    primary: "#0284C7", // ACC Vivid Azure
    bgLight: "#F0F9FF",
    glow: "rgba(2, 132, 199, 0.4)",
    tag: "OVERVIEW",
  },
  "Dataset Ingestion": {
    primary: "#0284C7", // Cyan / Ingestion Blue
    bgLight: "#F0F9FF",
    glow: "rgba(2, 132, 199, 0.45)",
    tag: "DATA INGESTION",
  },
  "Manual Entry": {
    primary: "#6366F1", // Indigo / Single Batch
    bgLight: "#EEF2FF",
    glow: "rgba(99, 102, 241, 0.45)",
    tag: "MANUAL ENTRY",
  },
  "Quality Analytics": {
    primary: "#059669", // Emerald / Compliance
    bgLight: "#ECFDF5",
    glow: "rgba(5, 150, 105, 0.45)",
    tag: "QUALITY ANALYTICS",
  },
  "Mix Optimization": {
    primary: "#D97706", // Amber / AI Optimization
    bgLight: "#FFFBEB",
    glow: "rgba(217, 119, 6, 0.45)",
    tag: "AI OPTIMIZATION",
  },
  "Governance & Audit": {
    primary: "#7C3AED", // Royal Purple / Governance Gate
    bgLight: "#F5F3FF",
    glow: "rgba(124, 58, 237, 0.45)",
    tag: "GOVERNANCE & AUDIT",
  },
  "Platform Administration": {
    primary: "#4F46E5", // Slate Indigo / RBAC
    bgLight: "#EEF2FF",
    glow: "rgba(79, 70, 229, 0.45)",
    tag: "ADMINISTRATION",
  },
  "System Settings": {
    primary: "#0D9488", // Teal / Calibre & Standards
    bgLight: "#F0FDFA",
    glow: "rgba(13, 148, 136, 0.45)",
    tag: "ENGINEERING CALIBRE",
  },
  "Platform Help": {
    primary: "#0284C7",
    bgLight: "#F0F9FF",
    glow: "rgba(2, 132, 199, 0.4)",
    tag: "HELP & CONTROLS",
  },
};

const STORAGE_PREFIX = "acc_rmc_tour_completed_";

export const hasUserCompletedTour = (userId?: string): boolean => {
  if (typeof window === "undefined" || !window.localStorage) return false;
  const key = `${STORAGE_PREFIX}${userId || "anonymous"}`;
  return localStorage.getItem(key) === "true";
};

export const markUserTourCompleted = (userId?: string): void => {
  if (typeof window === "undefined" || !window.localStorage) return;
  const key = `${STORAGE_PREFIX}${userId || "anonymous"}`;
  localStorage.setItem(key, "true");
};

export const resetUserTour = (userId?: string): void => {
  if (typeof window === "undefined" || !window.localStorage) return;
  const key = `${STORAGE_PREFIX}${userId || "anonymous"}`;
  localStorage.removeItem(key);
};

export const INITIAL_TOUR_STEPS: TourStep[] = [
  // SECTION 3: Operations Dashboard & Quality Analytics
  {
    id: "welcome-brand",
    targetSelector: '[data-tour="navbar-brand"]',
    route: "/acc",
    category: "Platform Overview",
    badge: "Step 1 of 22 • Platform Hub",
    title: "ACC RMC AI Platform",
    content: "Welcome to the ACC Ready-Mix Concrete AI Platform — unifying plant data ingestion, automated mix optimization, quality governance, and engineering calibration.",
    placement: "bottom",
  },
  {
    id: "dashboard-filters",
    targetSelector: '[data-tour="dashboard-filters"]',
    route: "/acc",
    category: "Platform Overview",
    badge: "Step 2 of 22 • Scope Filters",
    title: "Operational Scope Filters",
    content: "Filter all plant analytics by Plant Location, Recipe Grade (e.g., M-30, M-40), and Production Date ranges with instant reactive updates.",
    placement: "bottom",
  },
  {
    id: "dashboard-summary-cards",
    targetSelector: '[data-tour="dashboard-summary-cards"]',
    route: "/acc",
    category: "Platform Overview",
    badge: "Step 3 of 22 • Executive Summary",
    title: "Authoritative Operational Summary",
    content: "High-level summary uniting Quality & Production, 28-Day Strength Prediction, AI Mix Optimization runs, and Governance review state.",
    placement: "bottom",
  },
  {
    id: "dashboard-kpis",
    targetSelector: '[data-tour="dashboard-kpis"]',
    route: "/acc",
    category: "Platform Overview",
    badge: "Step 4 of 22 • Production KPIs",
    title: "Production Volume & Compliance KPIs",
    content: "Track total concrete volume (m³), total batch count, active plants, and IS 456 statistical quality compliance at a glance.",
    placement: "bottom",
  },
  {
    id: "dashboard-sqc-section",
    targetSelector: '[data-tour="dashboard-sqc-section"]',
    route: "/acc",
    category: "Quality Analytics",
    badge: "Step 5 of 22 • Quality Control",
    title: "Statistical Quality Control (IS 456)",
    content: "Inspect 28-day compressive strength distributions, standard deviation (σ), coefficient of variation (CV%), and historical strength timelines.",
    placement: "top",
  },
  {
    id: "dashboard-materials-section",
    targetSelector: '[data-tour="dashboard-materials-section"]',
    route: "/acc",
    category: "Quality Analytics",
    badge: "Step 6 of 22 • Material Analytics",
    title: "Material Consumption & Annex E Variance",
    content: "Monitor IS 4926:2003 Annex E scale weighing tolerances, water-binder (W/B) ratios, and cementitious binder intensity (kg/m³).",
    placement: "top",
  },
  {
    id: "dashboard-model-monitoring",
    targetSelector: '[data-tour="dashboard-model-monitoring"]',
    route: "/acc",
    category: "Quality Analytics",
    badge: "Step 7 of 22 • ML Telemetry",
    title: "28-Day Strength Predictor & Model Monitoring",
    content: "Inspect machine learning validation scatter (Actual vs Predicted), residual error distributions, and feature importance rankings.",
    placement: "top",
  },

  // SECTION 4: AI Mix Optimization & Governance Workspace
  {
    id: "dashboard-optimization-workspace",
    targetSelector: '[data-tour="dashboard-optimization-workspace"]',
    route: "/acc",
    category: "Mix Optimization",
    badge: "Step 8 of 22 • Optimization Workspace",
    title: "AI Mix Optimization & Target Setup",
    content: "Configure target mix design recipes and optimization objectives (Minimize Binder, Minimize Cost, or Balanced multi-objective).",
    placement: "top",
  },
  {
    id: "optimization-pareto-chart",
    targetSelector: '[data-tour="optimization-pareto-chart"]',
    route: "/acc",
    category: "Mix Optimization",
    badge: "Step 9 of 22 • Pareto Frontier",
    title: "Pareto Frontier & Multi-Candidate Solver",
    content: "Visualizes the non-dominated Pareto frontier comparing cementitious binder intensity (kg/m³) against predicted 28-day compressive strength.",
    placement: "top",
  },
  {
    id: "optimization-candidate-table",
    targetSelector: '[data-tour="optimization-candidate-table"]',
    route: "/acc",
    category: "Mix Optimization",
    badge: "Step 10 of 22 • Mix Formulation",
    title: "Candidate Constituent Proportions",
    content: "Inspect granular mix designs with cement, SCM (fly ash/GGBS), fine and coarse aggregates, water, and admixtures satisfying 1.000 m³ volume balance.",
    placement: "top",
  },
  {
    id: "optimization-diagnostics",
    targetSelector: '[data-tour="optimization-diagnostics"]',
    route: "/acc",
    category: "Mix Optimization",
    badge: "Step 11 of 22 • Constraint Diagnostics",
    title: "IS 456 & IS 10262 Engineering Diagnostics",
    content: "Automated standard compliance checking: minimum cementitious content, maximum W/B ratio limits, and aggregate grading envelope tolerances.",
    placement: "top",
  },
  {
    id: "optimization-impact-comparison",
    targetSelector: '[data-tour="optimization-impact-comparison"]',
    route: "/acc",
    category: "Mix Optimization",
    badge: "Step 12 of 22 • Commercial Impact",
    title: "Binder Savings & Cost Impact Analysis",
    content: "Side-by-side delta comparison evaluating binder reduction, cost per m³ variance, and carbon footprint reduction against current plant baseline.",
    placement: "top",
  },
  {
    id: "optimization-governance-gate",
    targetSelector: '[data-tour="optimization-governance-gate"]',
    route: "/acc",
    category: "Governance & Audit",
    badge: "Step 13 of 22 • Governance Gate",
    title: "Human Review & Quality Sign-Off",
    content: "Four-eyes governance gate allowing Quality Heads and Technical Directors to approve or reject proposed mixes with audit-logged remarks.",
    placement: "top",
  },

  // SECTION 1: Dataset Ingestion
  {
    id: "ingestion-pipeline-card",
    targetSelector: '[data-tour="ingestion-pipeline-card"]',
    route: "/acc/dataset-ingestion",
    category: "Dataset Ingestion",
    badge: "Step 14 of 22 • Ingestion Pipeline",
    title: "Automated Dataset Ingestion",
    content: "Bulk upload plant batching workbooks and QA cube registers with automated schema reconciliation and validation before staging.",
    placement: "top",
  },

  // SECTION 2: Manual Production Batch Entry
  {
    id: "manual-entry-hero-card",
    targetSelector: '[data-tour="manual-entry-hero-card"]',
    route: "/acc/manual-production-entry",
    category: "Manual Entry",
    badge: "Step 15 of 22 • Manual Entry",
    title: "Manual Batch & QA Logging",
    content: "Record individual SCADA batch tickets, aggregate moisture corrections, and 7D/28D laboratory compressive strength breaks.",
    placement: "top",
  },

  // SECTION 5: Administration — User Management
  {
    id: "admin-users-metrics",
    targetSelector: '[data-tour="admin-users-metrics"]',
    route: "/acc/admin/users",
    category: "Platform Administration",
    badge: "Step 16 of 22 • RBAC & Identity",
    title: "User Management & Identity Metrics",
    content: "Track enterprise user provisioning, active accounts, Super Admin authority tiers, and temporary credential lifecycle states.",
    placement: "bottom",
  },
  {
    id: "admin-users-table",
    targetSelector: '[data-tour="admin-users-table"]',
    route: "/acc/admin/users",
    category: "Platform Administration",
    badge: "Step 17 of 22 • User Directory",
    title: "User Directory & Access Control",
    content: "Search, filter, and manage team members across roles (SUPER_ADMIN, QUALITY_HEAD, PLANT_OPERATOR, VIEWER) with one-time credential reset and lifecycle management.",
    placement: "top",
  },

  // SECTION 6: Administration — Audit & Governance Center
  {
    id: "audit-domain-tabs",
    targetSelector: '[data-tour="audit-domain-tabs"]',
    route: "/acc/admin/audit",
    category: "Governance & Audit",
    badge: "Step 18 of 22 • Domain Compliance",
    title: "Audit Domains & Security Filter Tabs",
    content: "Segregate compliance trails across Authentication, User Admin, Data Ingestion, Manual Entry, and AI Model Training with dedicated domain tabs.",
    placement: "bottom",
  },
  {
    id: "audit-table-section",
    targetSelector: '[data-tour="audit-table-section"]',
    route: "/acc/admin/audit",
    category: "Governance & Audit",
    badge: "Step 19 of 22 • Forensic Ledger",
    title: "Immutable Operational Ledger & Trace",
    content: "Complete chronological audit events with correlation ID tracing, actor IP tracking, state change diffs, and full forensic audit inspection.",
    placement: "top",
  },

  // SECTION 7: Administration — Settings & Calculation Calibre
  {
    id: "settings-calibre-standard",
    targetSelector: '[data-tour="settings-calibre-standard"]',
    route: "/acc/admin/settings",
    category: "System Settings",
    badge: "Step 20 of 22 • Engineering Calibre",
    title: "IS Standards & Statistical Margin (Z-Factor)",
    content: "Configure IS 456 / IS 10262 governing standards, target mean strength Z-multiplier (1.28 to 1.65), and physical air volume yield (1.5%) dynamically used by the AI solver.",
    placement: "top",
  },
  {
    id: "settings-schema-viewer",
    targetSelector: '[data-tour="settings-schema-viewer"]',
    route: "/acc/admin/settings",
    category: "System Settings",
    badge: "Step 21 of 22 • Schema Viewer",
    title: "PostgreSQL Live Schema Viewer",
    content: "Authoritative read-only live introspection of production database tables, column constraints, primary/foreign keys, and storage volume.",
    placement: "top",
  },
  {
    id: "settings-sql-export",
    targetSelector: '[data-tour="settings-sql-export"]',
    route: "/acc/admin/settings",
    category: "System Settings",
    badge: "Step 22 of 22 • SQL DDL Export",
    title: "SQL DDL Export & Schema Governance",
    content: "Generate clean PostgreSQL DDL schemas for migrations, audits, and disaster recovery with instant single-click .sql file downloads.",
    placement: "top",
  },

  // Platform Controls / Replay
  {
    id: "nav-quick-tour",
    targetSelector: '[data-tour="navbar-quick-tour"]',
    route: "/acc",
    category: "Platform Help",
    badge: "Tour Complete • Replay Controls",
    title: "Replay Guided Tour Anytime",
    content: "You have completed the full walkthrough! You can relaunch this interactive guided tour at any time from the top navigation bar.",
    placement: "bottom",
  },
];
