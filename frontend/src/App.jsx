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

  return (
    <div className="page">
      <header className="hero">
        <p className="eyebrow">First Beta</p>
        <h1>RAG Decision Support Console</h1>
        <p className="subtitle">
          Ingest documents, index them, and query grounded answers with citations.
        </p>
      </header>

      <main className="grid">
        <section className="card">
          <h2>Ingest</h2>
          <form onSubmit={handlePayloadIngest} className="stack">
            <label>
              Payload text
              <textarea
                rows="8"
                value={payloadText}
                onChange={(event) => setPayloadText(event.target.value)}
              />
            </label>
            <label>
              Metadata JSON
              <textarea
                rows="4"
                value={metadataText}
                onChange={(event) => setMetadataText(event.target.value)}
              />
            </label>
            <button disabled={busy} type="submit">
              Ingest Payload
            </button>
          </form>
          <label className="file-picker">
            Upload file
            <input type="file" onChange={handleFileIngest} />
          </label>
        </section>

        <section className="card">
          <div className="section-head">
            <h2>Indexed Documents</h2>
            <button disabled={busy} onClick={() => handleReindex(null)} type="button">
              Reindex All
            </button>
          </div>
          <div className="list">
            {documents.map((document) => (
              <article key={document.id} className="list-item">
                <div>
                  <strong>{document.source_ref}</strong>
                  <p>{document.status}</p>
                  <small>
                    chunks: {document.chunk_count} | embeddings: {document.embedding_count}
                  </small>
                </div>
                <button disabled={busy} onClick={() => handleReindex(document.id)} type="button">
                  Reindex
                </button>
              </article>
            ))}
            {documents.length === 0 ? <p>No documents yet.</p> : null}
          </div>
        </section>

        <section className="card wide">
          <h2>Query</h2>
          <form onSubmit={handleQuery} className="query-form">
            <input
              type="text"
              placeholder="Ask a grounded question"
              value={queryForm.query}
              onChange={(event) => setQueryForm({ ...queryForm, query: event.target.value })}
            />
            <input
              type="number"
              min="1"
              max="20"
              value={queryForm.top_k}
              onChange={(event) => setQueryForm({ ...queryForm, top_k: event.target.value })}
            />
            <input
              type="text"
              placeholder='Filters JSON, e.g. {"country":"NO"}'
              value={queryForm.filters}
              onChange={(event) => setQueryForm({ ...queryForm, filters: event.target.value })}
            />
            <button disabled={busy} type="submit">
              Run Query
            </button>
          </form>

          {queryResult ? (
            <div className="result">
              <h3>Answer</h3>
              <p>{queryResult.answer}</p>
              <h3>Sources</h3>
              <div className="list">
                {queryResult.sources.map((source) => (
                  <article key={source.chunk} className="source">
                    <strong>{source.document}</strong>
                    <p>{source.excerpt}</p>
                    <small>
                      chunk: {source.chunk} | score: {source.score}
                    </small>
                  </article>
                ))}
              </div>
              <h3>Trace</h3>
              <pre>{JSON.stringify(queryResult.trace, null, 2)}</pre>
            </div>
          ) : null}
        </section>

        <section className="card">
          <h2>Jobs</h2>
          <div className="list">
            {jobs.map((job) => (
              <article key={job.id} className="list-item">
                <div>
                  <strong>{job.id}</strong>
                  <p>{job.status}</p>
                </div>
              </article>
            ))}
            {jobs.length === 0 ? <p>No reindex jobs run yet.</p> : null}
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
