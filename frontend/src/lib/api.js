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

export async function readError(response) {
  const payload = await response.json().catch(() => ({}));
  return payload.detail || "Request failed.";
}
