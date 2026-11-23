/**
 * Production REST API Client Service for Dataset Ingestion Subsystem (Step 1, Step 2, and Step 3).
 * Uses centralized apiClient for authenticated request execution.
 * 100% Zero Mock Data — All calls execute live backend HTTP requests against REST API endpoints.
 */

import { apiClient } from "./apiClient";

export interface RegisteredDatasetDTO {
  dataset_id: string;
  dataset_name: string;
  dataset_period: string;
  dataset_type_id: string;
  target_plant_id: string;
  import_profile_id: string;
  operator_id: string;
  remarks: string;
  status: string;
}

export interface UploadSessionDTO {
  session_id: string;
  dataset_id: string;
  operator_id: string;
  status: string;
  files: any[];
}

export interface DiscoveredFileDTO {
  file_id: string;
  session_id: string;
  filename: string;
  file_size_bytes: number;
  checksum_sha256: string;
  file_format: string;
  worksheet_names: string[];
  worksheet_count: number;
  status: string;
  step_description: string;
}

export interface ColumnLedgerItemDTO {
  incoming_header: string;
  canonical_target_id: string | null;
  canonical_target_name: string;
  resolution_strategy: string;
  similarity_score: number;
  requires_review: boolean;
  is_mandatory: boolean;
  is_feature: boolean;
  is_ignored: boolean;
}

export interface StandardizedPreviewRowDTO {
  mapping_execution_id: string;
  source_file_id: string;
  filename: string;
  worksheet_name: string;
  physical_excel_row: number;
  canonical_fields: Record<string, any>;
}

export interface SheetMappingPreviewDTO {
  file_id: string;
  filename: string;
  worksheet_name: string;
  is_applicable: boolean;
  detected_columns_count: number;
  auto_mapped_count: number;
  requires_review_count: number;
  missing_mandatory_count: number;
  feature_columns_count: number;
  ignored_columns_count: number;
  direct_matches_count: number;
  fuzzy_matches_count: number;
  overall_confidence_score: number;
  date_parser_pattern: string | null;
  date_parser_preview: string | null;
  ledger: ColumnLedgerItemDTO[];
  sample_rows: StandardizedPreviewRowDTO[];
}

export interface WorkbookPreviewDTO {
  file_id: string;
  filename: string;
  total_discovered_sheets: number;
  operational_sheets_count: number;
  excluded_sheets_count: number;
  workbook_classification: string;
  is_derived_only: boolean;
  default_active_worksheet: string | null;
  available_operational_worksheets: string[];
}

export interface SessionMappingPreviewDTO {
  session_id: string;
  dataset_id: string;
  import_profile_id: string;
  mapping_execution_id: string;
  mapping_engine_version: string;
  total_files_mapped: number;
  total_sheets_mapped: number;
  discovered_count: number;
  operational_count: number;
  processed_count: number;
  excluded_count: number;
  workbook_classification: string;
  is_derived_only: boolean;
  can_proceed_confirmation: boolean;
  active_worksheet_name: string | null;
  active_worksheet_scope: string | null;
  informational_message: string | null;
  operational_coverage_str: string;
  total_detected_columns: number;
  total_auto_mapped: number;
  total_requires_review: number;
  operational_requires_review?: number;
  total_missing_mandatory: number;
  overall_session_confidence: number;
  workbook_previews: WorkbookPreviewDTO[];
  sheet_previews: SheetMappingPreviewDTO[];
}

class ProductionDatasetIngestionApiService {
  /** Step 1: Register persistent dataset context */
  public async registerDataset(payload: {
    dataset_name: string;
    dataset_period: string;
    dataset_type_id: string;
    target_plant_id: string;
    import_profile_id: string;
    operator_id: string;
    remarks: string;
  }): Promise<RegisteredDatasetDTO> {
    return await apiClient.post<RegisteredDatasetDTO>("/ingestion/datasets", payload);
  }

  /** Step 2: Create persistent upload session bound to dataset_id */
  public async createSession(datasetId: string, operatorId: string): Promise<UploadSessionDTO> {
    return await apiClient.post<UploadSessionDTO>("/ingestion/sessions", {
      dataset_id: datasetId,
      operator_id: operatorId,
    });
  }

  /** Step 2: Upload binary file, compute checksum, run WorkbookScanner discovery */
  public async discoverWorkbook(
    sessionId: string,
    file: File
  ): Promise<{ file: DiscoveredFileDTO; workbook_metadata: any }> {
    const formData = new FormData();
    formData.append("file", file);

    return await apiClient.post<{ file: DiscoveredFileDTO; workbook_metadata: any }>(
      `/ingestion/sessions/${sessionId}/discover`,
      formData
    );
  }

  /** Step 3: Execute WS-03.2 Mapping Engine, persist result to DB, and return authoritative preview */
  public async createSessionMappingPreview(sessionId: string): Promise<SessionMappingPreviewDTO> {
    return await apiClient.post<SessionMappingPreviewDTO>(`/ingestion/sessions/${sessionId}/mapping/preview`);
  }

  /** Step 4: Fetch authoritative confirmation summary for session */
  public async getConfirmationSummary(sessionId: string): Promise<any> {
    return await apiClient.get<any>(`/ingestion/sessions/${sessionId}/confirmation`);
  }

  /** Step 4: Confirm mapping session, create persistent job_id, and start live ingestion */
  public async confirmSession(sessionId: string): Promise<{
    status: string;
    session_id: string;
    job_id: string;
    mapping_execution_id: string;
    message: string;
  }> {
    return await apiClient.post<{
      status: string;
      session_id: string;
      job_id: string;
      mapping_execution_id: string;
      message: string;
    }>(`/ingestion/sessions/${sessionId}/confirm`);
  }

  /** Step 5: Fetch authoritative status and execution metrics for an ingestion job */
  public async getJobStatus(jobId: string): Promise<{
    job_id: string;
    session_id: string;
    dataset_id: string;
    mapping_execution_id: string;
    status: string;
    current_stage: string;
    progress_percent: string;
    files_total: number;
    files_processed: number;
    worksheets_discovered: number;
    worksheets_processed: number;
    operational_records_detected: number;
    records_persisted: number;
    records_rejected: number;
    excluded_records: number;
    logs: string[];
    failure_reason?: string;
    created_at?: string;
    completed_at?: string;
  }> {
    return await apiClient.get<any>(`/ingestion/jobs/${jobId}/status`);
  }

  /** Safe Reset: Clear ingestion data and restore pristine test DB state */
  public async resetIngestionData(confirm: boolean, reason?: string): Promise<{
    status: string;
    database_environment: string;
    reset_timestamp: string;
    backup_location: string;
    tables_cleared: string[];
    rows_deleted_per_table: Record<string, number>;
    master_rows_preserved: Record<string, number>;
    orphan_count: number;
    synthetic_count: number;
    message: string;
  }> {
    return await apiClient.post<any>("/ingestion/reset", {
      confirm,
      reason: reason || "Frontend clean reset request",
      role: "admin",
    });
  }
}

export const datasetIngestionApi = new ProductionDatasetIngestionApiService();
