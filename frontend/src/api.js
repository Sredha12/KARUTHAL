const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(message, status = 500, data = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export function getAuthToken() {
  return localStorage.getItem("karuthal_token");
}

export function getOfficerSession() {
  const token = localStorage.getItem("karuthal_token");
  const name = localStorage.getItem("karuthal_officer_name");
  const district = localStorage.getItem("karuthal_district");
  if (!token) return null;
  return { token, name, district };
}

export function setOfficerSession(token, name, district) {
  localStorage.setItem("karuthal_token", token);
  localStorage.setItem("karuthal_officer_name", name);
  localStorage.setItem("karuthal_district", district);
}

export function clearOfficerSession() {
  localStorage.removeItem("karuthal_token");
  localStorage.removeItem("karuthal_officer_name");
  localStorage.removeItem("karuthal_district");
}

export async function apiRequest(endpoint, { method = "GET", body = null, reporterToken = null, headers = {} } = {}) {
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE_URL}${endpoint}`;
  const requestHeaders = {
    "Content-Type": "application/json",
    ...headers,
  };

  const token = getAuthToken();
  if (token && !requestHeaders["Authorization"]) {
    requestHeaders["Authorization"] = `Bearer ${token}`;
  }

  if (reporterToken) {
    requestHeaders["X-Reporter-Token"] = reporterToken;
  }

  const config = {
    method,
    headers: requestHeaders,
  };

  if (body !== null && method !== "GET" && method !== "HEAD") {
    config.body = typeof body === "string" ? body : JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(url, config);
  } catch (err) {
    throw new ApiError(`Network connection error: ${err.message}`, 0);
  }

  // Parse JSON response or fallback to text
  let responseData = null;
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    try {
      responseData = await response.json();
    } catch {
      responseData = null;
    }
  } else {
    try {
      const text = await response.text();
      responseData = text ? { message: text } : null;
    } catch {
      responseData = null;
    }
  }

  if (!response.ok) {
    const status = response.status;
    let message = "An error occurred with the request.";

    if (responseData) {
      message = responseData.message || responseData.detail || responseData.error || message;
    }

    if (status === 401) {
      clearOfficerSession();
      if (
        !window.location.pathname.startsWith("/login") &&
        window.location.pathname !== "/" &&
        !window.location.pathname.startsWith("/emergency")
      ) {
        window.location.href = "/login?session_expired=1";
      }
    } else if (status === 403) {
      message = message.includes("district")
        ? message
        : "Access denied: this resource is not allowed for your assigned district.";
    }

    throw new ApiError(message, status, responseData);
  }

  return responseData;
}

export const api = {
  get: (endpoint, options) => apiRequest(endpoint, { ...options, method: "GET" }),
  post: (endpoint, body, options) => apiRequest(endpoint, { ...options, method: "POST", body }),
  patch: (endpoint, body, options) => apiRequest(endpoint, { ...options, method: "PATCH", body }),
  delete: (endpoint, options) => apiRequest(endpoint, { ...options, method: "DELETE" }),
  baseUrl: API_BASE_URL,
};
