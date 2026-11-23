/**
 * Audit & Governance API Client Service.
 */

import { apiClient } from "./apiClient";
import {
  AuditEventItem,
  AuditEventListResponse,
  AuditMetrics,
  AuditCorrelationResponse,
  AuditQueryParams,
} from "../types/audit";

export const auditService = {
  /**
   * Query paginated, filtered audit events.
   */
  async getEvents(params: AuditQueryParams = {}): Promise<AuditEventListResponse> {
    const queryParams: Record<string, string | number | boolean | undefined> = {
      page: params.page ?? 1,
      page_size: params.page_size ?? 25,
      sort_by: params.sort_by ?? "created_at",
      sort_desc: params.sort_desc ?? true,
    };

    if (params.q) queryParams.q = params.q;
    if (params.module) queryParams.module = params.module;
    if (params.event_type) queryParams.event_type = params.event_type;
    if (params.severity) queryParams.severity = params.severity;
    if (params.result) queryParams.result = params.result;
    if (params.date_from) queryParams.date_from = params.date_from;
    if (params.date_to) queryParams.date_to = params.date_to;
    if (params.actor_id) queryParams.actor_id = params.actor_id;
    if (params.correlation_id) queryParams.correlation_id = params.correlation_id;

    return await apiClient.get<AuditEventListResponse>("/audit/events", queryParams);
  },

  /**
   * Fetch single audit event details by ID.
   */
  async getEventById(eventId: string): Promise<AuditEventItem> {
    return await apiClient.get<AuditEventItem>(`/audit/events/${eventId}`);
  },

  /**
   * Fetch aggregated audit and governance metrics.
   */
  async getMetrics(): Promise<AuditMetrics> {
    return await apiClient.get<AuditMetrics>("/audit/metrics");
  },

  /**
   * Fetch end-to-end correlation trace.
   */
  async getCorrelationTrace(correlationId: string): Promise<AuditCorrelationResponse> {
    return await apiClient.get<AuditCorrelationResponse>(`/audit/correlation/${encodeURIComponent(correlationId)}`);
  },

  /**
   * Download sanitized CSV export.
   */
  getExportUrl(params: AuditQueryParams = {}): string {
    const searchParams = new URLSearchParams();
    searchParams.set("format", "csv");
    if (params.q) searchParams.set("q", params.q);
    if (params.module) searchParams.set("module", params.module);
    if (params.event_type) searchParams.set("event_type", params.event_type);
    if (params.severity) searchParams.set("severity", params.severity);
    if (params.result) searchParams.set("result", params.result);
    if (params.date_from) searchParams.set("date_from", params.date_from);
    if (params.date_to) searchParams.set("date_to", params.date_to);
    if (params.actor_id) searchParams.set("actor_id", params.actor_id);
    if (params.correlation_id) searchParams.set("correlation_id", params.correlation_id);

    return `/api/v1/audit/export?${searchParams.toString()}`;
  },
};
