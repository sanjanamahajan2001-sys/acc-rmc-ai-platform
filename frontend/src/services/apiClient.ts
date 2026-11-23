/**
 * Centralized Production API Client for ACC RMC Platform.
 *
 * Enforces:
 * 1. Unified backend base URL resolution (/api/v1).
 * 2. Automatic Bearer token attachment from secure session storage.
 * 3. Centralized 401 Unauthorized detection & session invalidation.
 * 4. Centralized 403 Forbidden structured error extraction.
 * 5. Clean, enterprise-grade error formatting without stack traces.
 */

const TOKEN_STORAGE_KEY = "acc_rmc_auth_token";

export class ApiError extends Error {
  public status: number;
  public code?: string;
  public data?: any;

  constructor(status: number, message: string, code?: string, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.data = data;
  }
}

// In-memory token cache backed by sessionStorage
let inMemoryToken: string | null = null;

export const getAuthToken = (): string | null => {
  if (inMemoryToken) {
    return inMemoryToken;
  }
  if (typeof window !== "undefined" && window.sessionStorage) {
    try {
      const stored = sessionStorage.getItem(TOKEN_STORAGE_KEY);
      if (stored) {
        inMemoryToken = stored;
        return stored;
      }
    } catch {
      // Ignore storage access errors in restricted iframe/sandbox
    }
  }
  return null;
};

export const setAuthToken = (token: string | null): void => {
  inMemoryToken = token;
  if (typeof window !== "undefined" && window.sessionStorage) {
    try {
      if (token) {
        sessionStorage.setItem(TOKEN_STORAGE_KEY, token);
      } else {
        sessionStorage.removeItem(TOKEN_STORAGE_KEY);
      }
    } catch {
      // Ignore storage access errors
    }
  }
};

export const clearAuthToken = (): void => {
  setAuthToken(null);
};

// Event listeners for session expiration / unauthorized events
type UnauthorizedHandler = () => void;
const unauthorizedHandlers: Set<UnauthorizedHandler> = new Set();

export const onUnauthorized = (handler: UnauthorizedHandler): (() => void) => {
  unauthorizedHandlers.add(handler);
  return () => unauthorizedHandlers.delete(handler);
};

const notifyUnauthorized = (): void => {
  clearAuthToken();
  unauthorizedHandlers.forEach((handler) => {
    try {
      handler();
    } catch (err) {
      console.error("Error executing unauthorized handler:", err);
    }
  });
};

// Base URL resolution
export const resolveBaseUrl = (): string => {
  if (typeof window !== "undefined" && window.location.hostname === "localhost" && window.location.port === "5173") {
    return "http://localhost:8005/api/v1";
  }
  return "/acc-api/v1";
};

export interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: any;
  params?: Record<string, string | number | boolean | undefined>;
}

export async function request<T = any>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const baseUrl = resolveBaseUrl();
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  let url = `${baseUrl}${cleanEndpoint}`;

  // Query parameter formatting
  if (options.params) {
    const searchParams = new URLSearchParams();
    Object.entries(options.params).forEach(([key, val]) => {
      if (val !== undefined && val !== null) {
        searchParams.append(key, String(val));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes("?") ? "&" : "?") + queryString;
    }
  }

  // Headers setup
  const headers = new Headers(options.headers || {});
  
  // Set Content-Type to application/json by default if body is not FormData
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  // Attach Bearer token if available
  const token = getAuthToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  // Serialize body
  let bodyPayload: BodyInit | null | undefined = options.body;
  if (options.body && !(options.body instanceof FormData) && typeof options.body !== "string") {
    bodyPayload = JSON.stringify(options.body);
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
      body: bodyPayload,
    });
  } catch (networkErr: any) {
    throw new ApiError(
      0,
      "Unable to connect to ACC RMC operational server. Please check your network connection.",
      "NETWORK_ERROR"
    );
  }

  // Centralized HTTP Status Interception
  if (!response.ok) {
    let errorDetail: any = null;
    let message = `Request failed with status ${response.status}`;
    let code = "API_ERROR";

    try {
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        errorDetail = await response.json();
        if (typeof errorDetail === "string") {
          message = errorDetail;
        } else if (errorDetail && typeof errorDetail === "object") {
          if (errorDetail.detail) {
            if (typeof errorDetail.detail === "string") {
              message = errorDetail.detail;
            } else if (typeof errorDetail.detail === "object") {
              message = errorDetail.detail.message || JSON.stringify(errorDetail.detail);
              code = errorDetail.detail.error || code;
            }
          } else if (errorDetail.message) {
            message = errorDetail.message;
          }
          if (errorDetail.error) {
            code = errorDetail.error;
          }
        }
      } else {
        const text = await response.text();
        if (text) message = text;
      }
    } catch {
      // Fallback message
    }

    // 401 Unauthorized handling
    if (response.status === 401) {
      notifyUnauthorized();
      throw new ApiError(401, message || "Your session has expired. Please sign in again.", "UNAUTHORIZED", errorDetail);
    }

    // 403 Forbidden handling
    if (response.status === 403) {
      throw new ApiError(403, message || "Access denied. You do not have permission for this resource.", code || "FORBIDDEN", errorDetail);
    }

    // 404, 422, 500, etc.
    throw new ApiError(response.status, message, code, errorDetail);
  }

  // 204 No Content
  if (response.status === 204) {
    return null as unknown as T;
  }

  // Parse JSON response
  try {
    const data = await response.json();
    return data as T;
  } catch {
    return {} as T;
  }
}

export const apiClient = {
  request,
  get: <T = any>(endpoint: string, params?: Record<string, any>, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: "GET", params }),
  post: <T = any>(endpoint: string, body?: any, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: "POST", body }),
  put: <T = any>(endpoint: string, body?: any, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: "PUT", body }),
  patch: <T = any>(endpoint: string, body?: any, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: "PATCH", body }),
  delete: <T = any>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: "DELETE" }),
};
