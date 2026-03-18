import { formatDate } from "../lib/formatters.js";

export function DocumentsPage({
  busy,
  deletingDocumentId,
  documents,
  handleDeleteDocument,
  handleReindex,
}) {
  const indexed = documents.filter((d) => d.status === "indexed").length;
  const stale = documents.filter((d) => d.status === "ingested").length;

  return (
    <div className="page-stack">
      <section className="card section-card page-header-card">
        <div className="section-intro compact">
          <p className="section-label">Documents</p>
          <h2>Document corpus</h2>
          <p>Browse, reindex, and manage every document in your knowledge base.</p>
        </div>
      </section>

      <div className="doc-summary-bar">
        <span className="doc-summary-stat">
          <strong>{documents.length}</strong> total
        </span>
        <span className="doc-summary-stat">
          <strong>{indexed}</strong> indexed
        </span>
        <span className="doc-summary-stat">
          <strong>{stale}</strong> pending
        </span>
        <button
          className="ghost-button"
          disabled={busy || documents.length === 0}
          onClick={() => handleReindex(null)}
          type="button"
        >
          Reindex All
        </button>
      </div>

      <section className="card section-card">
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
                  v{document.version} &middot; {formatDate(document.last_ingested_at)}
                </p>
                <small>
                  {document.chunk_count} chunks &middot; {document.embedding_count} embeddings
                </small>
              </div>
              <div className="item-actions">
                <button
                  className="ghost-button"
                  disabled={busy}
                  onClick={() => handleReindex(document.id)}
                  type="button"
                >
                  Reindex
                </button>
                <button
                  className="ghost-button danger-button"
                  disabled={busy}
                  onClick={() => handleDeleteDocument(document)}
                  type="button"
                >
                  {deletingDocumentId === document.id ? "Deleting\u2026" : "Delete"}
                </button>
              </div>
            </article>
          ))}
          {documents.length === 0 ? (
            <p className="empty-state">No documents ingested yet. Head to Ingestion to upload your first source.</p>
          ) : null}
        </div>
      </section>
    </div>
  );
}
