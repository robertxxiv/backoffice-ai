import { formatBytes } from "../lib/formatters.js";

function StatusDot({ value }) {
  const ok = value === "ok" || value === "healthy" || value === "connected" || value === true;
  const color = ok ? "var(--teal)" : value ? "var(--gold)" : "var(--text-muted)";
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: "0.45rem" }}>
      <span
        style={{
          display: "inline-block",
          width: 7,
          height: 7,
          borderRadius: "50%",
          background: color,
          boxShadow: ok ? `0 0 8px ${color}` : "none",
          flexShrink: 0,
        }}
      />
      {value === true ? "true" : value === false ? "false" : value || "unknown"}
    </span>
  );
}

export function SettingsPage({ apiUrl, health }) {
  const uploadLimits = health?.upload_limits || null;

  return (
    <div className="page-stack">
      <section className="card section-card page-header-card">
        <div className="section-intro compact">
          <p className="section-label">Settings</p>
          <h2>Operational configuration</h2>
          <p>Read-only runtime information for the current environment and API connection.</p>
        </div>
      </section>

      <div className="grid operational-grid">
        <section className="card section-card">
          <div className="section-intro compact">
            <p className="section-label">Connection</p>
            <h2>API and provider status</h2>
          </div>
          <div className="settings-list">
            <div className="settings-row">
              <span>API URL</span>
              <strong style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>{apiUrl}</strong>
            </div>
            <div className="settings-row">
              <span>API status</span>
              <strong><StatusDot value={health?.status} /></strong>
            </div>
            <div className="settings-row">
              <span>Database</span>
              <strong><StatusDot value={health?.database} /></strong>
            </div>
            <div className="settings-row">
              <span>Embedding provider</span>
              <strong style={{ fontFamily: "var(--font-mono)", fontSize: "0.82rem" }}>
                {health?.embedding_provider || "unknown"}
              </strong>
            </div>
            <div className="settings-row">
              <span>Generation provider</span>
              <strong style={{ fontFamily: "var(--font-mono)", fontSize: "0.82rem" }}>
                {health?.generation_provider || "unknown"}
              </strong>
            </div>
          </div>
        </section>

        <section className="card section-card">
          <div className="section-intro compact">
            <p className="section-label">Policy</p>
            <h2>Current limits and exposure</h2>
          </div>
          <div className="settings-list">
            <div className="settings-row">
              <span>API docs enabled</span>
              <strong><StatusDot value={health?.api_docs_enabled ?? false} /></strong>
            </div>
            <div className="settings-row">
              <span>Max upload file</span>
              <strong>{formatBytes(uploadLimits?.file_bytes)}</strong>
            </div>
            <div className="settings-row">
              <span>Max ingest request</span>
              <strong>{formatBytes(uploadLimits?.request_bytes)}</strong>
            </div>
            <div className="settings-row">
              <span>Max ingest JSON</span>
              <strong>{formatBytes(uploadLimits?.json_bytes)}</strong>
            </div>
          </div>
          <p className="panel-note">
            Use backend environment variables for changes. This page is intentionally read-only in the current beta.
          </p>
        </section>
      </div>
    </div>
  );
}
