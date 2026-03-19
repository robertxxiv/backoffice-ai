export function resolveApiUrl() {
  const configured = import.meta.env.VITE_API_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }
  if (typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "https:" : "http:";
    return `${protocol}//${window.location.hostname}:8000`;
  }
  return "http://localhost:8000";
}

const TOKEN_KEY = "backoffice_ai_access_token";

export function getStoredToken() {
  if (typeof window === "undefined") {
    return "";
  }
  return window.localStorage.getItem(TOKEN_KEY) || "";
}

export function storeToken(token) {
  if (typeof window === "undefined") {
    return;
  }
  if (token) {
    window.localStorage.setItem(TOKEN_KEY, token);
    return;
  }
  window.localStorage.removeItem(TOKEN_KEY);
}

export function authHeaders(token, extraHeaders = {}) {
  if (!token) {
    return extraHeaders;
  }
  return {
    ...extraHeaders,
    Authorization: `Bearer ${token}`,
  };
}

export async function readError(response) {
  const payload = await response.json().catch(() => ({}));
  return payload.detail || "Request failed.";
}
