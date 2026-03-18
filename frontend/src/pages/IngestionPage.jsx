import { useNavigate } from "react-router-dom";

export function IngestionPage({
  busy,
  handleFileIngest,
  handlePayloadIngest,
  metadataText,
  payloadText,
  setMetadataText,
  setPayloadText,
}) {
  const navigate = useNavigate();

  return (
    <div className="page-stack">
      <section className="card section-card page-header-card">
        <div className="section-intro compact">
          <p className="section-label">Ingestion</p>
          <h2>Capture new source material</h2>
          <p>Upload files, paste payloads, and add metadata. Manage your corpus on the <button className="link-button inline-link" onClick={() => navigate("/documents")} type="button">Documents</button> page.</p>
        </div>
      </section>

      <div className="grid operational-grid">
        <section className="card section-card">
          <div className="section-intro">
            <p className="section-label">Text ingest</p>
            <h2>Paste a payload</h2>
          </div>
          <form onSubmit={handlePayloadIngest} className="stack">
            <label>
              <span className="field-label">Payload text</span>
              <textarea
                rows="8"
                value={payloadText}
                onChange={(event) => setPayloadText(event.target.value)}
              />
            </label>
            <label>
              <span className="field-label">Metadata JSON</span>
              <textarea
                rows="4"
                placeholder='{"category": "invoice", "country": "NO"}'
                value={metadataText}
                onChange={(event) => setMetadataText(event.target.value)}
              />
            </label>
            <button className="primary-button" disabled={busy} type="submit">
              Ingest Payload
            </button>
          </form>
        </section>

        <section className="card section-card">
          <div className="section-intro">
            <p className="section-label">File ingest</p>
            <h2>Upload a file</h2>
          </div>
          <p className="upload-hint">
            Upload a document file to be chunked, embedded, and indexed. Supported
            formats depend on the backend pipeline configuration.
          </p>
          <div className="file-picker">
            <label className="file-drop-zone" style={{ position: "relative" }}>
              <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 13v2a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-2" />
                <polyline points="5 7 9 3 13 7" />
                <line x1="9" y1="3" x2="9" y2="12" />
              </svg>
              Choose file or drag here
              <input
                type="file"
                onChange={handleFileIngest}
                style={{ position: "absolute", inset: 0, opacity: 0, cursor: "pointer", width: "100%" }}
              />
            </label>
          </div>
          <label style={{ marginTop: "1rem" }}>
            <span className="field-label">Metadata JSON (optional)</span>
            <textarea
              rows="3"
              placeholder='{"category": "invoice", "country": "NO"}'
              value={metadataText}
              onChange={(event) => setMetadataText(event.target.value)}
            />
          </label>
        </section>
      </div>
    </div>
  );
}
