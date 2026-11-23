import { useEffect, useRef, useState } from "react";
import { requestSSETicket } from "../services/reportingService";
import { resolveBaseUrl } from "../services/apiClient";

export type SyncStatus = "LIVE" | "SYNCING" | "RECONNECTING" | "OFFLINE";

export interface DashboardInvalidateEvent {
  event_id: string;
  event_type: string;
  scopes: string[];
  plant_code?: string | null;
  occurred_at?: string;
  token_version?: number;
}

export const useDashboardEventStream = (onInvalidate?: (event: DashboardInvalidateEvent) => void) => {
  const [syncStatus, setSyncStatus] = useState<SyncStatus>("RECONNECTING");
  const [lastEvent, setLastEvent] = useState<DashboardInvalidateEvent | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const backoffDelayRef = useRef<number>(1000);
  const onInvalidateRef = useRef(onInvalidate);

  useEffect(() => {
    onInvalidateRef.current = onInvalidate;
  }, [onInvalidate]);

  const connectSSE = async () => {
    try {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }

      setSyncStatus("RECONNECTING");
      const ticket = await requestSSETicket();
      const sseUrl = `${resolveBaseUrl()}/events/stream?ticket=${encodeURIComponent(ticket)}`;
      const es = new EventSource(sseUrl);
      eventSourceRef.current = es;

      es.onopen = () => {
        setSyncStatus("LIVE");
        backoffDelayRef.current = 1000;
      };

      es.addEventListener("CONNECTED", () => {
        setSyncStatus("LIVE");
      });

      es.addEventListener("DASHBOARD_INVALIDATE", (e: MessageEvent) => {
        try {
          const payload: DashboardInvalidateEvent = JSON.parse(e.data);
          setLastEvent(payload);
          setSyncStatus("SYNCING");

          if (onInvalidateRef.current) {
            onInvalidateRef.current(payload);
          }

          setTimeout(() => {
            setSyncStatus("LIVE");
          }, 400);
        } catch (err) {
          console.error("Failed to parse SSE invalidate payload", err);
        }
      });

      es.onerror = () => {
        setSyncStatus("OFFLINE");
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
          eventSourceRef.current = null;
        }

        const nextDelay = Math.min(backoffDelayRef.current * 2, 15000);
        backoffDelayRef.current = nextDelay;
        if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = window.setTimeout(() => {
          connectSSE();
        }, nextDelay);
      };
    } catch (err) {
      setSyncStatus("OFFLINE");
      const nextDelay = Math.min(backoffDelayRef.current * 2, 15000);
      backoffDelayRef.current = nextDelay;
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = window.setTimeout(() => {
        connectSSE();
      }, nextDelay);
    }
  };

  useEffect(() => {
    connectSSE();

    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        if (onInvalidateRef.current) {
          onInvalidateRef.current({
            event_id: "reconcile",
            event_type: "VISIBILITY_RECONCILIATION",
            scopes: ["kpis", "materials"],
          });
        }
        if (!eventSourceRef.current || eventSourceRef.current.readyState === EventSource.CLOSED) {
          connectSSE();
        }
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, []);

  return { syncStatus, lastEvent, reconnect: connectSSE };
};
