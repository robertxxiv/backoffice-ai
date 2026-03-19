import { NavLink, useNavigate } from "react-router-dom";

import { navItems } from "../constants.js";

const navIcons = {
  "/dashboard": (
    <svg className="nav-icon" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="2" width="6" height="6" rx="1.5" />
      <rect x="10" y="2" width="6" height="3.5" rx="1" />
      <rect x="10" y="7.5" width="6" height="8.5" rx="1.5" />
      <rect x="2" y="10" width="6" height="6" rx="1.5" />
    </svg>
  ),
  "/ingestion": (
    <svg className="nav-icon" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 13v2a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-2" />
      <polyline points="5 7 9 3 13 7" />
      <line x1="9" y1="3" x2="9" y2="12" />
    </svg>
  ),
  "/search": (
    <svg className="nav-icon" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="8" cy="8" r="5.5" />
      <line x1="12.4" y1="12.4" x2="16" y2="16" />
    </svg>
  ),
  "/documents": (
    <svg className="nav-icon" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10 2H5a1.5 1.5 0 0 0-1.5 1.5v11A1.5 1.5 0 0 0 5 16h8a1.5 1.5 0 0 0 1.5-1.5V7Z" />
      <polyline points="10 2 10 7 14.5 7" />
      <line x1="12" y1="10.5" x2="6" y2="10.5" />
      <line x1="12" y1="13.5" x2="6" y2="13.5" />
    </svg>
  ),
  "/jobs": (
    <svg className="nav-icon" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="10" width="3.5" height="6" rx="0.75" />
      <rect x="7.25" y="6" width="3.5" height="10" rx="0.75" />
      <rect x="12.5" y="2" width="3.5" height="14" rx="0.75" />
    </svg>
  ),
  "/settings": (
    <svg className="nav-icon" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="9" cy="9" r="2.5" />
      <path d="M9 1.5v1.25M9 15.25V16.5M1.5 9h1.25M15.25 9H16.5M3.52 3.52l.88.88M13.6 13.6l.88.88M14.48 3.52l-.88.88M4.4 13.6l-.88.88" />
    </svg>
  ),
};

function navClass({ isActive }) {
  return `nav-link${isActive ? " nav-link-active" : ""}`;
}

export function AppShell({ children, currentUser, onLogout }) {
  const navigate = useNavigate();
  const isAdmin = currentUser?.role === "admin";
  const visibleNavItems = navItems.filter((item) => !item.adminOnly || isAdmin);

  return (
    <div className="page">
      <div className="background-orbit orbit-a" />
      <div className="background-orbit orbit-b" />
      <div className="background-grid" />

      <div className="app-shell shell">
        <aside className="sidebar card">
          <div className="sidebar-brand" role="button" tabIndex={0} onClick={() => navigate("/")} onKeyDown={(e) => e.key === "Enter" && navigate("/")}>
            <p className="eyebrow">Operational Knowledge</p>
            <h1>Backoffice.AI</h1>
            <p>Internal retrieval, ingestion, and operational visibility in one workspace.</p>
          </div>
          <nav className="sidebar-nav" aria-label="Primary">
            {visibleNavItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={navClass}
              >
                {navIcons[item.path]}
                {item.label}
              </NavLink>
            ))}
          </nav>
          {currentUser ? (
            <div className="sidebar-user">
              <div className="sidebar-user-copy">
                <strong>{currentUser.email}</strong>
                <span>{currentUser.role}</span>
              </div>
              <button className="ghost-button" onClick={onLogout} type="button">
                Sign out
              </button>
            </div>
          ) : null}
        </aside>

        <div className="app-content">{children}</div>
      </div>
    </div>
  );
}
