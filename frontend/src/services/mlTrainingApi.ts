/**
 * Production REST API Client Service for ML Model Training & Registry Subsystem (Phase 13E / 13F / 13G).
 * Uses centralized apiClient for authenticated request execution against backend /api/v1/ml.
 * 100% Zero Mock Data — All calls execute live backend HTTP requests against REST API endpoints.
 */

import { apiClient } from "./apiClient";

export interface MLTrainingJobLogEntry {
  timestamp: string;
  stage: string;
  severity: string;
  message: string;
}

export interface MLTrainingJobDTO {
  job_id: string;
  dataset_fingerprint: string;
  feature_schema_version: string;
  observation_count: number;
  status: "QUEUED" | "PRECHECKING" | "RUNNING" | "SUCCEEDED" | "FAILED" | "TIMED_OUT" | "CANCELLED" | "RESOURCE_REJECTED";
  current_stage?: string;
  records_processed?: number;
  records_total?: number;
  last_heartbeat_at?: string | null;
  execution_logs?: MLTrainingJobLogEntry[];
  failure_reason?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  execution_metadata: Record<string, any>;
}

export interface ModelRegistryDTO {
  id: string;
  model_name: string;
  model_version: string;
  framework: string;
  algorithm: string;
  feature_schema_version: string;
  training_dataset_version?: string | null;
  artifact_location?: string | null;
  checksum?: string | null;
  deployment_status: "CANDIDATE" | "ACTIVE" | "RETIRED";
  deployment_timestamp: string;
  created_at: string;
}

export interface CreateTrainingJobPayload {
  dataset_fingerprint: string;
  observation_count: number;
  dataset_origin_breakdown?: Record<string, any>;
  feature_schema_version?: string;
  execution_timeout_seconds?: number;
  is_dummy_test?: boolean;
}

class MLTrainingApiService {
  /** Create asynchronous training job */
  public async submitTrainingJob(payload: CreateTrainingJobPayload): Promise<MLTrainingJobDTO> {
    return await apiClient.post<MLTrainingJobDTO>("/ml/jobs", payload);
  }

  /** Retrieve durable status of a specific training job */
  public async getJobStatus(jobId: string): Promise<MLTrainingJobDTO> {
    return await apiClient.get<MLTrainingJobDTO>(`/ml/jobs/${jobId}`);
  }

  /** List historical training jobs */
  public async listJobs(limit: number = 20): Promise<MLTrainingJobDTO[]> {
    return await apiClient.get<MLTrainingJobDTO[]>("/ml/jobs", { limit });
  }

  /** Retrieve currently ACTIVE production model */
  public async getActiveModel(): Promise<ModelRegistryDTO | null> {
    return await apiClient.get<ModelRegistryDTO | null>("/ml/registry/active");
  }

  /** List all models from registry */
  public async listModels(): Promise<ModelRegistryDTO[]> {
    return await apiClient.get<ModelRegistryDTO[]>("/ml/registry/models");
  }

  /** Retrieve single model detail */
  public async getModelDetail(modelIdOrVersion: string): Promise<ModelRegistryDTO> {
    return await apiClient.get<ModelRegistryDTO>(`/ml/registry/models/${modelIdOrVersion}`);
  }

  /** Explicitly activate a candidate model */
  public async activateModel(modelId: string, reason: string = "Explicit production approval"): Promise<ModelRegistryDTO> {
    return await apiClient.post<ModelRegistryDTO>(`/ml/registry/models/${modelId}/activate`, { reason });
  }

  /** Rollback active model to a previous retired model */
  public async rollbackModel(targetModelId?: string, reason: string = "Reverting active model to previous verified retired model"): Promise<ModelRegistryDTO> {
    return await apiClient.post<ModelRegistryDTO>("/ml/registry/rollback", {
      target_model_id: targetModelId,
      reason,
    });
  }
}

export const mlTrainingApi = new MLTrainingApiService();
