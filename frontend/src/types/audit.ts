/**
 * Audit & Governance Center TypeScript Interfaces & Types.
 */

export type AuditModule =
  | "AUTH"
  | "USER_ADMIN"
  | "DATA_INGESTION"
  | "MANUAL_ENTRY"
  | "MODEL_TRAINING"
  | "ML_TRAINING_JOB"
  | "ML_MODEL_REGISTRY"
  | "QUALITY_QA"
  | "MASTER_DATA"
  | "SECURITY"
  | "SYSTEM";

export type AuditSeverity = "INFO" | "WARNING" | "CRITICAL";

export type AuditResult = "SUCCESS" | "FAILURE" | "DENIED" | "REJECTED" | "QUARANTINED" | "PARTIAL";

export interface ActorInfo {
  user_id: string | null;
  username: string;
  email?: string | null;
  full_name?: string | null;
  roles: string[];
  ip_address?: string | null;
  user_agent?: string | null;
}

export interface TargetInfo {
  entity_type: string;
  entity_id: string;
  entity_name?: string | null;
}

export interface AuditEventItem {
  id: string;
  timestamp: string;
  module: AuditModule | string;
  event_type: string;
  action: string;
  severity: AuditSeverity | string;
  result: AuditResult | string;
  actor: ActorInfo;
  target: TargetInfo;
  correlation_id?: string | null;
  details: Record<string, any>;
  ip_address?: string | null;
  user_agent?: string | null;
}

export interface AuditEventListResponse {
  items: AuditEventItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AuditMetrics {
  total_events: number;
  successful_events: number;
  failed_events: number;
  denied_events: number;
  events_last_24h: number;
  module_breakdown: Record<string, number>;
}

export interface AuditCorrelationResponse {
  correlation_id: string;
  total_events: number;
  events: AuditEventItem[];
}

export interface AuditQueryParams {
  page?: number;
  page_size?: number;
  q?: string;
  module?: string;
  event_type?: string;
  severity?: string;
  result?: string;
  date_from?: string;
  date_to?: string;
  actor_id?: string;
  correlation_id?: string;
  sort_by?: string;
  sort_desc?: boolean;
}
