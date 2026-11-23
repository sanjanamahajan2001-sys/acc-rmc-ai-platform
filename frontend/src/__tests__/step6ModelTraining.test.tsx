import { describe, it, expect, vi, beforeEach } from "vitest";
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { Step6ModelTraining } from "../components/dataset-ingestion/Step6ModelTraining";
import { mlTrainingApi } from "../services/mlTrainingApi";

// Mock mlTrainingApi
vi.mock("../services/mlTrainingApi", () => ({
  mlTrainingApi: {
    getActiveModel: vi.fn(),
    listModels: vi.fn(),
    submitTrainingJob: vi.fn(),
    getJobStatus: vi.fn(),
    activateModel: vi.fn(),
  },
}));

// Mock AuthContext
vi.mock("../context/AuthContext", () => ({
  useAuth: vi.fn(),
  AuthProvider: ({ children }: any) => <div>{children}</div>,
}));

import { useAuth } from "../context/AuthContext";

describe("Step6ModelTraining Component — Phase 13F / ML-6 Frontend Verification", () => {
  const mockClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as any).mockReturnValue({
      user: { id: "user-1", username: "admin_test", roles: ["QUALITY_HEAD"] },
      isSuperAdmin: false,
      isAdmin: false,
      isQualityHead: true,
      isLabTech: false,
      isAnalyst: false,
      isPlantOperator: false,
    });

    (mlTrainingApi.getActiveModel as any).mockResolvedValue({
      id: "active-mod-1",
      model_name: "acc_concrete_28d_strength",
      model_version: "v_prod_active_1.0.0",
      framework: "xgboost",
      algorithm: "XGBoostRegressor",
      feature_schema_version: "1.0.0",
      deployment_status: "ACTIVE",
      deployment_timestamp: "2026-09-16T10:00:00Z",
      created_at: "2026-09-16T10:00:00Z",
    });

    (mlTrainingApi.listModels as any).mockResolvedValue([
      {
        id: "active-mod-1",
        model_name: "acc_concrete_28d_strength",
        model_version: "v_prod_active_1.0.0",
        framework: "xgboost",
        algorithm: "XGBoostRegressor",
        feature_schema_version: "1.0.0",
        deployment_status: "ACTIVE",
        deployment_timestamp: "2026-09-16T10:00:00Z",
        created_at: "2026-09-16T10:00:00Z",
      },
      {
        id: "cand-mod-2",
        model_name: "acc_concrete_28d_strength",
        model_version: "v_cand_2.0.0",
        framework: "xgboost",
        algorithm: "XGBoostRegressor",
        feature_schema_version: "1.0.0",
        deployment_status: "CANDIDATE",
        deployment_timestamp: "2026-09-16T11:00:00Z",
        created_at: "2026-09-16T11:00:00Z",
      },
    ]);
  });

  it("1. Step 6 renders correctly and displays current active model", async () => {
    render(<Step6ModelTraining onCloseWizard={mockClose} />);
    expect(screen.getByText("CURRENT ACTIVE PRODUCTION MODEL")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("v_prod_active_1.0.0")).toBeInTheDocument();
    });
  });

  it("2. Authorized Quality Head can see and trigger training action", async () => {
    (mlTrainingApi.submitTrainingJob as any).mockResolvedValue({
      job_id: "job-12345",
      dataset_fingerprint: "a".repeat(64),
      feature_schema_version: "1.0.0",
      observation_count: 50,
      status: "QUEUED",
      created_at: new Date().toISOString(),
      execution_metadata: {},
    });

    render(<Step6ModelTraining onCloseWizard={mockClose} />);
    const trainBtn = screen.getByText("Start Model Training");
    expect(trainBtn).toBeInTheDocument();

    fireEvent.click(trainBtn);
    await waitFor(() => {
      expect(mlTrainingApi.submitTrainingJob).toHaveBeenCalled();
      expect(screen.getByText(/Training request has been accepted/i)).toBeInTheDocument();
    });
  });

  it("3. Unauthorized role (Plant Operator) cannot trigger training", async () => {
    (useAuth as any).mockReturnValue({
      user: { id: "user-op", username: "operator_test", roles: ["PLANT_OPERATOR"] },
      isSuperAdmin: false,
      isAdmin: false,
      isQualityHead: false,
      isLabTech: false,
      isAnalyst: false,
      isPlantOperator: true,
    });

    render(<Step6ModelTraining onCloseWizard={mockClose} />);
    expect(screen.getByText(/Access Restricted/i)).toBeInTheDocument();
    expect(screen.queryByText("Start Model Training")).not.toBeInTheDocument();
  });

  it("4. 409 Concurrent Training Job response is cleanly handled without stack trace", async () => {
    (mlTrainingApi.submitTrainingJob as any).mockRejectedValue({
      status: 409,
      message: "A training job is already running.",
    });

    render(<Step6ModelTraining onCloseWizard={mockClose} />);
    const trainBtn = screen.getByText("Start Model Training");
    fireEvent.click(trainBtn);

    await waitFor(() => {
      expect(screen.getByText(/A training job is already running/i)).toBeInTheDocument();
    });
  });

  it("5. Candidate model is displayed separately and never automatically activated", async () => {
    render(<Step6ModelTraining onCloseWizard={mockClose} />);
    await waitFor(() => {
      expect(screen.getByText("v_cand_2.0.0")).toBeInTheDocument();
      expect(screen.getAllByText("CANDIDATE").length).toBeGreaterThan(0);
      expect(screen.getByText("Review & Activate")).toBeInTheDocument();
    });
    // Verify no automatic activation occurred
    expect(mlTrainingApi.activateModel).not.toHaveBeenCalled();
  });

  it("6. Explicit activation requires confirmation dialog and reason input", async () => {
    (mlTrainingApi.activateModel as any).mockResolvedValue({
      id: "cand-mod-2",
      model_name: "acc_concrete_28d_strength",
      model_version: "v_cand_2.0.0",
      deployment_status: "ACTIVE",
    });

    render(<Step6ModelTraining onCloseWizard={mockClose} />);
    await waitFor(() => {
      expect(screen.getByText("Review & Activate")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Review & Activate"));
    expect(screen.getByText("⚠️ Confirm Production Model Activation")).toBeInTheDocument();

    const confirmBtn = screen.getByText("Confirm Activation");
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(mlTrainingApi.activateModel).toHaveBeenCalledWith("cand-mod-2", expect.any(String));
    });
  });

  it("7. Activation failure (422) is safely handled leaving UI intact", async () => {
    (mlTrainingApi.activateModel as any).mockRejectedValue({
      status: 422,
      message: "Checksum mismatch: model artifact is corrupt.",
    });

    render(<Step6ModelTraining onCloseWizard={mockClose} />);
    await waitFor(() => {
      expect(screen.getByText("Review & Activate")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Review & Activate"));
    fireEvent.click(screen.getByText("Confirm Activation"));

    await waitFor(() => {
      expect(screen.getByText(/Activation Failed: The model artifact failed integrity/i)).toBeInTheDocument();
    });
  });
});
