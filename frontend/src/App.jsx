import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";

const apiUrl = resolveApiUrl();

const emptyQuery = {
  query: "",
  top_k: 5,
  country: "",
  category: "",
  extraFilters: "",
};

const exampleQuestions = [
  "What VAT rule applies to the latest Norwegian invoice?",
  "Summarize the main information in the uploaded quote.",
  "Which document mentions Hertz?",
];

const retrievalPhases = [
  {
    label: "Searching indexed documents",
    detail: "Scanning the catalog and narrowing to the most relevant chunks.",
  },
  {
    label: "Ranking relevant evidence",
    detail: "Comparing context quality before building the final response.",
  },
  {
    label: "Composing grounded answer",
    detail: "Formatting a concise answer with source-backed evidence.",
  },
];

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
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [queryBusy, setQueryBusy] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState(0);

  useEffect(() => {
    void refreshDocuments();
  }, []);

  useEffect(() => {
    if (!queryBusy) {
      setLoadingPhase(0);
      return undefined;
    }

    const timer = window.setInterval(() => {
      setLoadingPhase((current) => (current + 1) % retrievalPhases.length);
    }, 1100);

    return () => window.clearInterval(timer);
  }, [queryBusy]);

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
    setQueryBusy(true);
    setError("");
    setQueryResult(null);
    try {
      const response = await fetch(`${apiUrl}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: queryForm.query,
          top_k: Number(queryForm.top_k),
          filters: buildQueryFilters(queryForm),
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
      setQueryBusy(false);
      setBusy(false);
    }
  }

  const stats = buildStats(documents);
  const filterOptions = buildFilterOptions(documents);

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
            <p>Ask in plain language. Narrow the scope only when you need to.</p>
          </div>
          <div className="prompt-suggestions">
            {exampleQuestions.map((question) => (
              <button
                key={question}
                className="suggestion-chip"
                onClick={() => setQueryForm({ ...queryForm, query: question })}
                type="button"
              >
                {question}
              </button>
            ))}
          </div>
          <form onSubmit={handleQuery} className="query-form">
            <label className="query-query">
              <span className="field-label">Ask your question</span>
              <input
                type="text"
                placeholder="Ask about uploaded and indexed documents"
                value={queryForm.query}
                onChange={(event) => setQueryForm({ ...queryForm, query: event.target.value })}
              />
            </label>
            <label>
              <span className="field-label">Category</span>
              <select
                value={queryForm.category}
                onChange={(event) => setQueryForm({ ...queryForm, category: event.target.value })}
              >
                <option value="">All categories</option>
                {filterOptions.categories.map((category) => (
                  <option key={category} value={category}>
                    {formatOptionLabel(category)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span className="field-label">Country</span>
              <select
                value={queryForm.country}
                onChange={(event) => setQueryForm({ ...queryForm, country: event.target.value })}
              >
                <option value="">Any country</option>
                {filterOptions.countries.map((country) => (
                  <option key={country} value={country}>
                    {country}
                  </option>
                ))}
              </select>
            </label>
            <button className="primary-button" disabled={busy} type="submit">
              Search Company Knowledge
            </button>
          </form>
          <div className="query-help">
            <p>Ask about indexed documents only. If you just uploaded a file, reindex it first.</p>
            <button
              className="link-button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              type="button"
            >
              {showAdvanced ? "Hide advanced options" : "Show advanced options"}
            </button>
          </div>

          {showAdvanced ? (
            <div className="advanced-panel">
              <div className="advanced-grid">
                <label>
                  <span className="field-label">Retrieval breadth</span>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={queryForm.top_k}
                    onChange={(event) => setQueryForm({ ...queryForm, top_k: event.target.value })}
                  />
                </label>
                <label>
                  <span className="field-label">Extra filters JSON</span>
                  <input
                    type="text"
                    placeholder='{"customer":"hertz"}'
                    value={queryForm.extraFilters}
                    onChange={(event) =>
                      setQueryForm({ ...queryForm, extraFilters: event.target.value })
                    }
                  />
                </label>
              </div>
            </div>
          ) : null}

          {queryBusy ? <QueryLoadingState activeIndex={loadingPhase} /> : null}

          {queryResult && !queryBusy ? (
            <div className="result">
              <div className="result-block">
                <p className="section-label">Answer</p>
                <MarkdownAnswer text={queryResult.answer} />
              </div>
              {queryResult.machine_output ? (
                <details className="machine-panel">
                  <summary>Show structured data</summary>
                  <pre>{JSON.stringify(queryResult.machine_output, null, 2)}</pre>
                </details>
              ) : null}
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
                    <small>From document evidence</small>
                  </article>
                ))}
              </div>
              <details className="trace-panel">
                <summary>Show technical details</summary>
                <pre>{JSON.stringify(queryResult.trace, null, 2)}</pre>
              </details>
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

function buildFilterOptions(documents) {
  const countries = new Set();
  const categories = new Set();

  documents.forEach((document) => {
    const metadata = document.metadata_summary || {};
    if (typeof metadata.country === "string" && metadata.country) {
      countries.add(metadata.country);
    }
    const category = firstString(metadata.category, metadata.domain, metadata.type);
    if (category) {
      categories.add(category);
    }
  });

  return {
    countries: Array.from(countries).sort(),
    categories: Array.from(categories).sort(),
  };
}

function buildQueryFilters(queryForm) {
  const filters = {};

  if (queryForm.country) {
    filters.country = queryForm.country;
  }
  if (queryForm.category) {
    filters.category = queryForm.category;
  }
  if (queryForm.extraFilters) {
    Object.assign(filters, parseJson(queryForm.extraFilters));
  }

  return filters;
}

function formatDate(value) {
  if (!value) {
    return "n/a";
  }
  return new Date(value).toLocaleDateString();
}

function formatOptionLabel(value) {
  return value
    .split(/[-_]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function firstString(...values) {
  return values.find((value) => typeof value === "string" && value) || "";
}

function QueryLoadingState({ activeIndex }) {
  return (
    <div className="loading-panel" aria-live="polite" aria-busy="true">
      <div className="loading-head">
        <p className="section-label">Working</p>
        <h3>Building your answer</h3>
      </div>
      <div className="loading-phase-list">
        {retrievalPhases.map((phase, index) => {
          const state = index < activeIndex ? "complete" : index === activeIndex ? "active" : "idle";

          return (
            <article key={phase.label} className={`loading-phase phase-${state}`}>
              <div className="phase-marker">
                <span />
              </div>
              <div className="phase-copy">
                <strong>{phase.label}</strong>
                <p>{phase.detail}</p>
                <div className="phase-skeletons" aria-hidden="true">
                  <span className="skeleton-line short" />
                  <span className="skeleton-line medium" />
                  <span className="skeleton-line long" />
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

function MarkdownAnswer({ text }) {
  return (
    <div className="answer-markdown">
      <ReactMarkdown components={markdownComponents}>{text}</ReactMarkdown>
    </div>
  );
}

const markdownComponents = {
  h1: ({ children }) => <h1 className="markdown-h1">{children}</h1>,
  h2: ({ children }) => <h2 className="markdown-h2">{children}</h2>,
  h3: ({ children }) => <h3 className="markdown-h3">{children}</h3>,
  p: ({ children }) => <p className="answer-paragraph">{children}</p>,
  ul: ({ children }) => <ul className="answer-list">{children}</ul>,
  li: ({ children }) => <li>{children}</li>,
  code: ({ inline, children }) =>
    inline ? (
      <code className="inline-code">{children}</code>
    ) : (
      <code className="code-block">{children}</code>
    ),
  pre: ({ children }) => <pre className="markdown-pre">{children}</pre>,
  strong: ({ children }) => <strong className="markdown-strong">{children}</strong>,
};

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
