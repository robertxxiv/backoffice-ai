export function JobsPage({ jobs }) {
  const completed = jobs.filter((j) => j.status === "completed").length;
  const failed = jobs.filter((j) => j.status === "failed").length;

  return (
    <div className="page-stack">
      <section className="card section-card page-header-card">
        <div className="section-intro compact">
          <p className="section-label">Jobs</p>
          <h2>Pipeline activity</h2>
          <p>Track indexing jobs, inspect statuses, and monitor the processing pipeline.</p>
        </div>
      </section>

      {jobs.length > 0 ? (
        <div className="doc-summary-bar">
          <span className="doc-summary-stat">
            <strong>{jobs.length}</strong> total
          </span>
          <span className="doc-summary-stat">
            <strong>{completed}</strong> completed
          </span>
          {failed > 0 ? (
            <span className="doc-summary-stat doc-summary-danger">
              <strong>{failed}</strong> failed
            </span>
          ) : null}
        </div>
      ) : null}

      <section className="card section-card">
        <div className="list">
          {jobs.map((job) => (
            <article key={job.id} className="list-item">
              <div className="item-copy">
                <div className="item-title-row">
                  <strong style={{ fontFamily: "var(--font-mono)", fontSize: "0.82rem", fontWeight: 500 }}>
                    {job.id}
                  </strong>
                  <span className={`status-pill status-${job.status}`}>
                    {job.status}
                  </span>
                </div>
                <p className="item-meta">{job.job_type} &middot; v{job.document_version}</p>
              </div>
            </article>
          ))}
          {jobs.length === 0 ? (
            <p className="empty-state">No reindex jobs have been run yet. Trigger a reindex from the Documents page.</p>
          ) : null}
        </div>
      </section>
    </div>
  );
}
