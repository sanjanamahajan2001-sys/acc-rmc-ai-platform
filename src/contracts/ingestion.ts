/**
 * Enterprise Data Acquisition & Ingestion Shared Type Contracts.
 *
 * This module defines shared TypeScript interfaces matching backend Pydantic DTO models.
 * Contains ZERO HTML, CSS, React components, or UI rendering code.
 */

export const CONTRACT_NAME = "ACC_RMC_Ingestion_Contracts";
export const INGESTION_CONTRACT_VERSION = "1.0.0";
export const CONTRACT_CREATED_AT = "2026-08-07T21:32:00Z";
export const CONTRACT_AUTHOR = "ACC AI Engineering Team";
export const CONTRACT_COMPATIBILITY = "WS-01, WS-02, WS-03";

export interface BatchIngestionDTO {
  batch_number: string;
  order_number: string;
  plant_code: string;
  recipe_code: string;
  planned_quantity_m3: number;
  actual_quantity_m3?: number | null;
  production_start_time?: string | null;
  production_end_time?: string | null;
  operator_id?: string | null;
}

export interface ProductionEventIngestionDTO {
  event_type: string;
  event_timestamp: string;
  sequence_number: number;
  device_id?: string | null;
  remarks?: string | null;
}

export interface MaterialConsumptionIngestionDTO {
  material_code: string;
  planned_quantity: number;
  actual_quantity: number;
  moisture_percentage?: number;
}

export interface WeighingLogIngestionDTO {
  material_code: string;
  target_weight_kg: number;
  actual_weight_kg: number;
  scale_device_id?: string | null;
  weighing_timestamp: string;
}

export interface SlumpTestIngestionDTO {
  slump_mm: number;
  test_timestamp: string;
  tester_name?: string | null;
  ambient_temperature_c?: number | null;
  concrete_temperature_c?: number | null;
}

export interface CubeTestIngestionDTO {
  cube_set_number: string;
  age_days: number;
  compressive_strength_mpa: number;
  testing_timestamp: string;
  tested_by_user?: string | null;
}

export interface FT7CertificateIngestionDTO {
  certificate_number: string;
  issued_date: string;
  approval_status: string;
  remarks?: string | null;
}

export interface SingleIngestionPayloadDTO {
  batch: BatchIngestionDTO;
  material_consumptions: MaterialConsumptionIngestionDTO[];
  weighing_logs?: WeighingLogIngestionDTO[];
  slump_tests?: SlumpTestIngestionDTO[];
  cube_tests?: CubeTestIngestionDTO[];
  ft7_certificate?: FT7CertificateIngestionDTO | null;
  production_events?: ProductionEventIngestionDTO[];
}

export interface IngestionBatchPayloadDTO {
  import_profile_id?: string | null;
  source_channel: "EXCEL_IMPORT" | "MANUAL_ENTRY";
  payloads: SingleIngestionPayloadDTO[];
}

export interface ValidationDiagnosticDTO {
  field_name: string;
  error_code: string;
  message: string;
  severity: "CRITICAL" | "WARNING" | "INFO";
  row_index?: number | null;
}

export interface IngestionResultResponseDTO {
  ingestion_status: "SUCCESS" | "QUARANTINED" | "FAILED";
  batch_number?: string | null;
  records_processed: number;
  diagnostics: ValidationDiagnosticDTO[];
  feature_vector_id?: string | null;
  processing_time_ms?: number | null;
  contract_version?: string;
  correlation_id?: string | null;
  trace_id?: string | null;
}
