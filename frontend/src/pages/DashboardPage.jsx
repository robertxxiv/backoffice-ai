import { useNavigate } from "react-router-dom";

const quickLinks = [
  { path: "/ingestion", label: "Capture new source", icon: "upload" },
  { path: "/search", label: "Run a grounded query", icon: "search" },
  { path: "/documents", label: "Browse documents", icon: "docs" },
  { path: "/jobs", label: "View pipeline jobs", icon: "jobs" },
];

const quickIcons = {
  upload: (
    <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 13v2a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-2" />
      <polyline points="5 7 9 3 13 7" />
      <line x1="9" y1="3" x2="9" y2="12" />
    </svg>
  ),
  search: (
    <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="5.5" />
      <line x1="12.4" y1="12.4" x2="16" y2="16" />
    </svg>
  ),
  docs: (
    <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 2H5a1.5 1.5 0 0 0-1.5 1.5v11A1.5 1.5 0 0 0 5 16h8a1.5 1.5 0 0 0 1.5-1.5V7Z" />
      <polyline points="10 2 10 7 14.5 7" />
    </svg>
  ),
  jobs: (
    <svg viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="10" width="3.5" height="6" rx="0.75" />
      <rect x="7.25" y="6" width="3.5" height="10" rx="0.75" />
      <rect x="12.5" y="2" width="3.5" height="14" rx="0.75" />
    </svg>
  ),
};

export function DashboardPage({ stats, documents, jobs }) {
  const navigate = useNavigate();

  const recentDocs = documents.slice(0, 4);
  const recentJobs = jobs.slice(0, 4);

  return (
    <div className="page-stack">
      <section className="card section-card page-header-card">
        <div className="section-intro compact">
          <p className="section-label">Dashboard</p>
          <h2>Workspace overview</h2>
          <p>System metrics, recent activity, and quick navigation to every section.</p>
        </div>
      </section>

      <section className="card section-card">
        <div className="metric-grid metric-grid-4">
          {stats.map((stat) => (
            <article key={stat.label} className="metric-card">
              <span>{stat.label}</span>
              <strong>{stat.value}</strong>
            </article>
          ))}
        </div>
      </section>

      <div className="quick-links-grid">
        {quickLinks.map((link) => (
          <button
            key={link.path}
            className="quick-link-card"
            onClick={() => navigate(link.path)}
            type="button"
          >
            <span className="quick-link-icon">{quickIcons[link.icon]}</span>
            <span className="quick-link-label">{link.label}</span>
            <svg className="quick-link-arrow" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <line x1="2" y1="6" x2="10" y2="6" />
              <polyline points="7 3 10 6 7 9" />
            </svg>
          </button>
        ))}
      </div>

      <div className="grid operational-grid">
        <section className="card section-card">
          <div className="section-head">
            <div className="section-intro compact">
              <p className="section-label">Corpus</p>
              <h2>Recent documents</h2>
            </div>
            <button className="ghost-button" onClick={() => navigate("/documents")} type="button">
              View all
            </button>
          </div>
          <div className="list">
            {recentDocs.map((doc) => (
              <article key={doc.id} className="list-item">
                <div className="item-copy">
                  <div className="item-title-row">
                    <strong>{doc.source_ref}</strong>
                    <span className={`status-pill status-${doc.status}`}>{doc.status}</span>
                  </div>
                  <small>{doc.chunk_count} chunks &middot; {doc.embedding_count} embeddings</small>
                </div>
              </article>
            ))}
            {recentDocs.length === 0 ? <p className="empty-state">No documents yet.</p> : null}
          </div>
        </section>

        <section className="card section-card">
          <div className="section-head">
            <div className="section-intro compact">
              <p className="section-label">Pipeline</p>
              <h2>Recent jobs</h2>
            </div>
            <button className="ghost-button" onClick={() => navigate("/jobs")} type="button">
              View all
            </button>
          </div>
          <div className="list">
            {recentJobs.map((job) => (
              <article key={job.id} className="list-item">
                <div className="item-copy">
                  <div className="item-title-row">
                    <strong style={{ fontFamily: "var(--font-mono)", fontSize: "0.82rem", fontWeight: 500 }}>
                      {job.id}
                    </strong>
                    <span className={`status-pill status-${job.status}`}>{job.status}</span>
                  </div>
                  <p className="item-meta">{job.job_type} &middot; v{job.document_version}</p>
                </div>
              </article>
            ))}
            {recentJobs.length === 0 ? <p className="empty-state">No jobs yet.</p> : null}
          </div>
        </section>
      </div>
    </div>
  );
}
