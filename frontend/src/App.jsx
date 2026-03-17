import { useEffect, useState } from "react";

const apiUrl = resolveApiUrl();

const emptyQuery = {
  query: "",
  top_k: 5,
  filters: "",
};

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [payloadText, setPayloadText] = useState(
    "Norwegian VAT for consulting is 25 percent. Winter season pricing applies from December to February.",
  );
  const [metadataText, setMetadataText] = useState('{"country":"NO","domain":"quotes"}');
  const [queryForm, setQueryForm] = useState(emptyQuery);
  const [queryResult, setQueryResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    void refreshDocuments();
  }, []);

  async function refreshDocuments() {
    const response = await fetch(`${apiUrl}/documents`);
    const payload = await response.json();
    setDocuments(payload);
  }

  async function handlePayloadIngest(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${apiUrl}/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          payload: payloadText,
          metadata: parseJson(metadataText),
          source_name: `manual-${Date.now()}`,
        }),
      });
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      await refreshDocuments();
    } catch (caught) {
      setError(caught.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleFileIngest(event) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setBusy(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("metadata", metadataText);
      const response = await fetch(`${apiUrl}/ingest`, {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      await refreshDocuments();
      event.target.value = "";
    } catch (caught) {
      setError(caught.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleReindex(documentId = null) {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${apiUrl}/reindex`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: documentId,
          run_inline: true,
          strategy: "overlap",
          chunk_size: 512,
          overlap_tokens: 64,
        }),
      });
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      const payload = await response.json();
      setJobs(payload.jobs);
      await refreshDocuments();
    } catch (caught) {
      setError(caught.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleQuery(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${apiUrl}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: queryForm.query,
          top_k: Number(queryForm.top_k),
          filters: queryForm.filters ? parseJson(queryForm.filters) : {},
        }),
      });
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      const payload = await response.json();
      setQueryResult(payload);
    } catch (caught) {
      setError(caught.message);
    } finally {
      setBusy(false);
    }
  }

  const stats = buildStats(documents);

  return (
    <div className="page">
      <div className="background-orbit orbit-a" />
      <div className="background-orbit orbit-b" />
      <div className="background-grid" />

      <header className="hero shell">
        <div className="hero-copy">
          <p className="eyebrow">Operational Knowledge Workspace</p>
          <h1>Backoffice AI</h1>
          <p className="subtitle">
            Grounded retrieval for internal documents, with indexing controls, query tracing,
            and source-linked answers built for daily backoffice work.
          </p>
        </div>
        <aside className="hero-panel">
          <p className="panel-label">System Snapshot</p>
          <div className="metric-grid">
            {stats.map((stat) => (
              <article key={stat.label} className="metric-card">
                <span>{stat.label}</span>
                <strong>{stat.value}</strong>
              </article>
            ))}
          </div>
          <p className="panel-note">
            Query responses remain grounded only in indexed material. Reindex after each
            content change.
          </p>
        </aside>
      </header>

      <main className="shell grid">
        <section className="card section-card">
          <div className="section-intro">
            <p className="section-label">Ingestion</p>
            <h2>Capture new source material</h2>
            <p>Paste raw content or upload supported files for normalization and storage.</p>
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
                value={metadataText}
                onChange={(event) => setMetadataText(event.target.value)}
              />
            </label>
            <button className="primary-button" disabled={busy} type="submit">
              Ingest Payload
            </button>
          </form>
          <label className="file-picker">
            <span className="field-label">Upload file</span>
            <input type="file" onChange={handleFileIngest} />
          </label>
        </section>

        <section className="card section-card">
          <div className="section-head">
            <div className="section-intro compact">
              <p className="section-label">Index</p>
              <h2>Document inventory</h2>
            </div>
            <button
              className="ghost-button"
              disabled={busy}
              onClick={() => handleReindex(null)}
              type="button"
            >
              Reindex All
            </button>
          </div>
          <div className="list">
            {documents.map((document) => (
              <article key={document.id} className="list-item">
                <div className="item-copy">
                  <div className="item-title-row">
                    <strong>{document.source_ref}</strong>
                    <span className={`status-pill status-${document.status}`}>
                      {document.status}
                    </span>
                  </div>
                  <p className="item-meta">
                    version {document.version} | updated {formatDate(document.last_ingested_at)}
                  </p>
                  <small>
                    {document.chunk_count} chunks | {document.embedding_count} embeddings
                  </small>
                </div>
                <button
                  className="ghost-button"
                  disabled={busy}
                  onClick={() => handleReindex(document.id)}
                  type="button"
                >
                  Reindex
                </button>
              </article>
            ))}
            {documents.length === 0 ? <p className="empty-state">No documents yet.</p> : null}
          </div>
        </section>

        <section className="card wide section-card">
          <div className="section-intro">
            <p className="section-label">Retrieval</p>
            <h2>Run a grounded query</h2>
            <p>Adjust retrieval breadth only when needed. Smaller contexts are cheaper and sharper.</p>
          </div>
          <form onSubmit={handleQuery} className="query-form">
            <label className="query-query">
              <span className="field-label">Ask a grounded question</span>
              <input
                type="text"
                placeholder="Which VAT rule applies to the latest Norwegian invoice?"
                value={queryForm.query}
                onChange={(event) => setQueryForm({ ...queryForm, query: event.target.value })}
              />
            </label>
            <label>
              <span className="field-label">top_k</span>
              <input
                type="number"
                min="1"
                max="20"
                value={queryForm.top_k}
                onChange={(event) => setQueryForm({ ...queryForm, top_k: event.target.value })}
              />
            </label>
            <label>
              <span className="field-label">Filters JSON</span>
              <input
                type="text"
                placeholder='{"country":"NO"}'
                value={queryForm.filters}
                onChange={(event) => setQueryForm({ ...queryForm, filters: event.target.value })}
              />
            </label>
            <button className="primary-button" disabled={busy} type="submit">
              Run Query
            </button>
          </form>

          {queryResult ? (
            <div className="result">
              <div className="result-block">
                <p className="section-label">Answer</p>
                <p className="answer-copy">{queryResult.answer}</p>
              </div>
              <div className="result-block">
                <p className="section-label">Sources</p>
              </div>
              <div className="list">
                {queryResult.sources.map((source) => (
                  <article key={source.chunk} className="source">
                    <div className="item-title-row">
                      <strong>{source.document}</strong>
                      <span className="score-pill">{Number(source.score).toFixed(3)}</span>
                    </div>
                    <p>{source.excerpt}</p>
                    <small>chunk: {source.chunk}</small>
                  </article>
                ))}
              </div>
              <div className="result-block">
                <p className="section-label">Trace</p>
                <pre>{JSON.stringify(queryResult.trace, null, 2)}</pre>
              </div>
            </div>
          ) : null}
        </section>

        <section className="card section-card">
          <div className="section-intro compact">
            <p className="section-label">Pipeline</p>
            <h2>Recent jobs</h2>
          </div>
          <div className="list">
            {jobs.map((job) => (
              <article key={job.id} className="list-item">
                <div className="item-copy">
                  <strong>{job.id}</strong>
                  <p className="item-meta">
                    {job.job_type} | version {job.document_version}
                  </p>
                  <small>{job.status}</small>
                </div>
              </article>
            ))}
            {jobs.length === 0 ? (
              <p className="empty-state">No reindex jobs run yet.</p>
            ) : null}
          </div>
        </section>
      </main>

      {error ? <div className="error">{error}</div> : null}
    </div>
  );
}

function parseJson(value) {
  return JSON.parse(value);
}

function buildStats(documents) {
  const indexed = documents.filter((document) => document.status === "indexed").length;
  const stale = documents.filter((document) => document.is_index_stale).length;
  const chunks = documents.reduce((total, document) => total + document.chunk_count, 0);

  return [
    { label: "Documents", value: documents.length },
    { label: "Indexed", value: indexed },
    { label: "Stale", value: stale },
    { label: "Chunks", value: chunks },
  ];
}

function formatDate(value) {
  if (!value) {
    return "n/a";
  }
  return new Date(value).toLocaleDateString();
}

async function readError(response) {
  const payload = await response.json().catch(() => ({}));
  return payload.detail || "Request failed.";
}

function resolveApiUrl() {
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
