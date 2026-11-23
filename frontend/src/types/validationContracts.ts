/**
 * TypeScript Contracts for Multi-Tier Validation Preview (Phase 4).
 */

export interface CanonicalRowDTO {
  row_index: number;
  fields: Record<string, any>;
  audit_records: Record<string, any>[];
}

export interface ValidationPreviewRowDTO {
  preview_row_id: string;
  validation_trace_id: string;
  worksheet_name: string;
  excel_row_number: number;
  canonical_row: CanonicalRowDTO;
  validation_status: "PASSED" | "WARNING" | "QUARANTINED" | "CRITICAL";
  is_valid: boolean;
  quality_score: number;
  severity: "NONE" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";
  quarantine_recommended: boolean;
  warnings: Record<string, any>[];
  errors: Record<string, any>[];
}

export interface ValidatedWorksheetChunkDTO {
  worksheet_name: string;
  chunk_index: number;
  starting_row: number;
  ending_row: number;
  total_rows: number;
  valid_rows_count: number;
  quarantined_rows_count: number;
  preview_rows: ValidationPreviewRowDTO[];
  tier5_dataset_errors: Record<string, any>[];
}

export interface PreviewStatisticsDTO {
  total_rows_evaluated: number;
  valid_rows_count: number;
  warning_rows_count: number;
  quarantined_rows_count: number;
  overall_quality_score: number;
  validation_duration_ms: number;
  preview_generation_duration_ms: number;
  rows_per_second: number;
}

export interface ValidationSummaryDTO {
  session_id?: string | null;
  file_id?: string | null;
  filename: string;
  profile_id?: string | null;
  statistics: PreviewStatisticsDTO;
  validated_chunks: ValidatedWorksheetChunkDTO[];
  validated_at: string;
}

export interface ValidationPreviewDTO {
  session_id?: string | null;
  file_id?: string | null;
  filename: string;
  summary: ValidationSummaryDTO;
  preview_rows: ValidationPreviewRowDTO[];
  created_at: string;
}

export interface ValidationSessionSummaryDTO {
  session_id: string;
  user_id: string;
  total_files: number;
  successful_files: number;
  partially_valid_files: number;
  failed_files: number;
  total_files_evaluated: number;
  total_rows: number;
  total_rows_evaluated: number;
  total_valid_rows: number;
  total_quarantined_rows: number;
  total_quarantined: number;
  overall_quality_score: number;
  per_file_statistics: Record<string, any>[];
  file_summaries: ValidationSummaryDTO[];
  evaluated_at: string;
}
