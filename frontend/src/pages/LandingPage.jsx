import { useNavigate } from "react-router-dom";

const features = [
  {
    title: "Ingestion",
    description: "Upload files, paste payloads, and feed your knowledge base with structured or raw content.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
        <polyline points="7 9 12 4 17 9" />
        <line x1="12" y1="4" x2="12" y2="16" />
      </svg>
    ),
  },
  {
    title: "Grounded Search",
    description: "Ask natural-language questions and get answers backed by indexed evidence and source citations.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="7" />
        <line x1="16.5" y1="16.5" x2="21" y2="21" />
      </svg>
    ),
  },
  {
    title: "Document Corpus",
    description: "Browse, reindex, and manage your entire document inventory with version tracking and chunk visibility.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
      </svg>
    ),
  },
  {
    title: "Pipeline Visibility",
    description: "Track indexing jobs, monitor pipeline health, and inspect operational metrics in real time.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="14" width="4" height="7" rx="1" />
        <rect x="10" y="9" width="4" height="12" rx="1" />
        <rect x="17" y="4" width="4" height="17" rx="1" />
      </svg>
    ),
  },
];

export function LandingPage({ stats }) {
  const navigate = useNavigate();

  return (
    <div className="landing">
      <div className="landing-bg-orbit landing-orbit-a" />
      <div className="landing-bg-orbit landing-orbit-b" />
      <div className="landing-bg-orbit landing-orbit-c" />

      <div className="landing-content">
        <header className="landing-hero">
          <div className="landing-badge">
            <span className="landing-badge-dot" />
            Operational Knowledge Platform
          </div>
          <h1 className="landing-title">
            Backoffice<span className="landing-title-accent">.AI</span>
          </h1>
          <p className="landing-subtitle">
            Internal retrieval-augmented generation workspace. Ingest documents,
            run grounded queries, and maintain full operational visibility
            — all in one focused interface.
          </p>
          <div className="landing-actions">
            <button
              className="primary-button landing-cta"
              onClick={() => navigate("/dashboard")}
              type="button"
            >
              Enter workspace
              <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="3" y1="8" x2="13" y2="8" />
                <polyline points="9 4 13 8 9 12" />
              </svg>
            </button>
            <button
              className="ghost-button"
              onClick={() => navigate("/search")}
              type="button"
            >
              Jump to search
            </button>
          </div>
        </header>

        <section className="landing-features">
          {features.map((feature) => (
            <article key={feature.title} className="landing-feature-card">
              <div className="landing-feature-icon">{feature.icon}</div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </article>
          ))}
        </section>

        {stats.length > 0 ? (
          <section className="landing-metrics">
            <p className="landing-metrics-label">Live system snapshot</p>
            <div className="landing-metrics-row">
              {stats.map((stat) => (
                <div key={stat.label} className="landing-metric">
                  <span className="landing-metric-value">{stat.value}</span>
                  <span className="landing-metric-label">{stat.label}</span>
                </div>
              ))}
            </div>
          </section>
        ) : null}

        <footer className="landing-footer">
          <p>Backoffice.AI &middot; Internal RAG system</p>
        </footer>
      </div>
    </div>
  );
}
