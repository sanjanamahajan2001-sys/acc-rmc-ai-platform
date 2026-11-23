/**
 * Dataset Ingestion Frontend Client Service.
 * Consumes immutable preview contracts emitted by WS-03.4 backend services.
 */

import { FileIngestionLifecycle, FileUploadTaskDTO, UploadSessionDTO } from "../types/uploadContracts";
import { ValidationPreviewDTO } from "../types/validationContracts";

class DatasetIngestionApiService {
  private activeSessions: Map<string, UploadSessionDTO> = new Map();

  /** Create new multi-file ingestion upload session */
  public async createSession(userId: string): Promise<UploadSessionDTO> {
    const sessionId = `SES-${Date.now()}-${Math.random().toString(36).substring(2, 7).toUpperCase()}`;
    const session: UploadSessionDTO = {
      session_id: sessionId,
      user_id: userId,
      status: "CREATED" as any,
      files: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    self.activeSessions?.set ? self.activeSessions.set(sessionId, session) : this.activeSessions.set(sessionId, session);
    return session;
  }

  /** Enqueue mock/uploaded file into session */
  public async enqueueFile(sessionId: string, file: File): Promise<FileUploadTaskDTO> {
    const session = this.activeSessions.get(sessionId);
    if (!session) throw new Error(`Session ${sessionId} not found`);

    const fileId = `FILE-${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
    const task: FileUploadTaskDTO = {
      file_id: fileId,
      session_id: sessionId,
      filename: file.name,
      file_size_bytes: file.size,
      status: FileIngestionLifecycle.QUEUED,
      progress_percentage: 0,
      current_step_description: "Enqueued in upload queue",
      worksheet_names: ["BatchData", "Summary"],
      total_rows_found: 150,
      rows_mapped: 150,
      rows_valid: 140,
      rows_invalid: 10,
      quality_score: 93.3,
      enqueued_at: new Date().toISOString(),
    };

    session.files.push(task);
    session.status = "ACTIVE" as any;
    return task;
  }

  /** Simulate lifecycle progress for file task */
  public async simulateFileLifecycle(
    sessionId: string,
    fileId: string,
    onProgress: (task: FileUploadTaskDTO) => void
  ): Promise<ValidationPreviewDTO> {
    const session = this.activeSessions.get(sessionId);
    const task = session?.files.find((f) => f.file_id === fileId);
    if (!task) throw new Error("Task not found");

    const steps: { status: FileIngestionLifecycle; desc: string; progress: number }[] = [
      { status: FileIngestionLifecycle.UPLOADING, desc: "Uploading Excel file...", progress: 15 },
      { status: FileIngestionLifecycle.UPLOAD_COMPLETED, desc: "Upload completed", progress: 25 },
      { status: FileIngestionLifecycle.CHECKSUM_VERIFICATION, desc: "Verifying SHA-256 checksum...", progress: 35 },
      { status: FileIngestionLifecycle.SCANNING, desc: "Scanning workbook tabs & headers...", progress: 45 },
      { status: FileIngestionLifecycle.READING_WORKBOOK, desc: "Reading openpyxl stream...", progress: 55 },
      { status: FileIngestionLifecycle.READING_WORKSHEETS, desc: "Extracting RawWorksheetChunk rows...", progress: 65 },
      { status: FileIngestionLifecycle.MAPPING, desc: "Mapping to WS-03.2 Canonical Fields...", progress: 75 },
      { status: FileIngestionLifecycle.VALIDATING, desc: "Executing WS-03.3 Multi-Tier Validation...", progress: 88 },
      { status: FileIngestionLifecycle.GENERATING_PREVIEW, desc: "Generating immutable validation preview...", progress: 100 },
    ];

    for (const step of steps) {
      task.status = step.status;
      task.current_step_description = step.desc;
      task.progress_percentage = step.progress;
      onProgress({ ...task });
      await new Promise((r) => setTimeout(r, 80));
    }

    return this.generateMockPreview(task);
  }

  /** Generate immutable preview contract payload matching backend DTO */
  private generateMockPreview(task: FileUploadTaskDTO): ValidationPreviewDTO {
    const rows = Array.from({ length: 15 }, (_, idx) => {
      const rowNum = idx + 2;
      const isValid = idx !== 5 && idx !== 11;
      return {
        preview_row_id: `PRV-ROW-${rowNum}`,
        validation_trace_id: `TRC-TRACE-${rowNum}`,
        worksheet_name: "BatchData",
        excel_row_number: rowNum,
        canonical_row: {
          row_index: idx,
          fields: {
            FIELD_BATCH_ID: `BAT-2026-${(idx + 1).toString().padStart(4, "0")}`,
            FIELD_PLANT_ID: "PLANT-MUM-01",
            FIELD_ACTUAL_CEMENT_KG: isValid ? 420.0 : -50.0,
            FIELD_ACTUAL_WATER_KG: isValid ? 168.0 : 0.0,
            FIELD_SLUMP_MM: 150.0,
          },
          audit_records: [],
        },
        validation_status: isValid ? ("PASSED" as const) : ("QUARANTINED" as const),
        is_valid: isValid,
        quality_score: isValid ? 100.0 : 45.0,
        severity: isValid ? ("NONE" as const) : ("CRITICAL" as const),
        quarantine_recommended: !isValid,
        warnings: isValid ? [] : [{ field_id: "FIELD_ACTUAL_CEMENT_KG", message: "Cement weight cannot be negative" }],
        errors: isValid ? [] : [{ field_id: "FIELD_ACTUAL_CEMENT_KG", message: "Cement weight -50kg violates Tier 2 non-negative rule", severity: "CRITICAL" }],
      };
    });

    return {
      session_id: task.session_id,
      file_id: task.file_id,
      filename: task.filename,
      summary: {
        session_id: task.session_id,
        file_id: task.file_id,
        filename: task.filename,
        profile_id: "PROFILE-MUMBAI-SCADA",
        statistics: {
          total_rows_evaluated: 15,
          valid_rows_count: 13,
          warning_rows_count: 0,
          quarantined_rows_count: 2,
          overall_quality_score: 93.3,
          validation_duration_ms: 4.5,
          preview_generation_duration_ms: 0.8,
          rows_per_second: 3333.3,
        },
        validated_chunks: [],
        validated_at: new Date().toISOString(),
      },
      preview_rows: rows,
      created_at: new Date().toISOString(),
    };
  }
}

export const datasetIngestionApi = new DatasetIngestionApiService();
