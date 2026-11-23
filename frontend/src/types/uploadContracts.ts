/**
 * TypeScript Contracts for Upload Session & Queue Management (Phase 1).
 */

export enum UploadSessionLifecycle {
  CREATED = "CREATED",
  ACTIVE = "ACTIVE",
  PROCESSING = "PROCESSING",
  PREVIEW_READY = "PREVIEW_READY",
  COMPLETED = "COMPLETED",
  PARTIAL_SUCCESS = "PARTIAL_SUCCESS",
  FAILED = "FAILED",
  CANCELLED = "CANCELLED",
  EXPIRED = "EXPIRED",
}

export enum FileIngestionLifecycle {
  QUEUED = "QUEUED",
  UPLOADING = "UPLOADING",
  UPLOAD_COMPLETED = "UPLOAD_COMPLETED",
  CHECKSUM_VERIFICATION = "CHECKSUM_VERIFICATION",
  SCANNING = "SCANNING",
  READING_WORKBOOK = "READING_WORKBOOK",
  READING_WORKSHEETS = "READING_WORKSHEETS",
  MAPPING = "MAPPING",
  VALIDATING = "VALIDATING",
  GENERATING_PREVIEW = "GENERATING_PREVIEW",
  COMPLETED = "COMPLETED",
  PARTIAL_SUCCESS = "PARTIAL_SUCCESS",
  FAILED = "FAILED",
  CANCELLED = "CANCELLED",
  RETRY_PENDING = "RETRY_PENDING",
  DUPLICATE_REJECTED = "DUPLICATE_REJECTED",
}

export interface FileUploadTaskDTO {
  file_id: string;
  session_id: string;
  filename: string;
  file_size_bytes: number;
  checksum_sha256?: string | null;
  status: FileIngestionLifecycle;
  progress_percentage: number;
  current_step_description: string;
  worksheet_names: string[];
  selected_worksheet?: string | null;
  import_profile_id?: string | null;
  total_rows_found: number;
  rows_mapped: number;
  rows_valid: number;
  rows_invalid: number;
  quality_score?: number | null;
  error_message?: string | null;
  enqueued_at: string;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface UploadSessionDTO {
  session_id: string;
  user_id: string;
  status: UploadSessionLifecycle;
  files: FileUploadTaskDTO[];
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
}

export interface UploadSessionSummaryContractDTO {
  session_id: string;
  user_id: string;
  created_at: string;
  completed_at?: string | null;
  total_files: number;
  completed_files: number;
  failed_files: number;
  cancelled_files: number;
  duplicate_files: number;
  total_rows_processed: number;
  total_rows_valid: number;
  total_rows_invalid: number;
  overall_quality_score: number;
  processing_duration_ms: number;
  file_summaries: Record<string, any>[];
}
