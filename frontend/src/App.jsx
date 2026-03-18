import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";

import { AppShell } from "./components/AppShell.jsx";
import { useBackofficeApp } from "./hooks/useBackofficeApp.js";
import { DashboardPage } from "./pages/DashboardPage.jsx";
import { DocumentsPage } from "./pages/DocumentsPage.jsx";
import { IngestionPage } from "./pages/IngestionPage.jsx";
import { JobsPage } from "./pages/JobsPage.jsx";
import { LandingPage } from "./pages/LandingPage.jsx";
import { SearchPage } from "./pages/SearchPage.jsx";
import { SettingsPage } from "./pages/SettingsPage.jsx";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [pathname]);
  return null;
}

function AppRoutes() {
  const app = useBackofficeApp();

  return (
    <>
      <ScrollToTop />
      <Routes>
        {/* Landing page — full-screen, no sidebar */}
        <Route path="/" element={<LandingPage stats={app.stats} />} />

        {/* App pages — wrapped in sidebar shell */}
        <Route
          path="/*"
          element={
            <AppShell>
              <Routes>
                <Route path="/dashboard" element={<DashboardPage stats={app.stats} documents={app.documents} jobs={app.jobs} />} />
                <Route path="/ingestion" element={<IngestionPage {...app} />} />
                <Route path="/search" element={<SearchPage {...app} />} />
                <Route path="/documents" element={<DocumentsPage busy={app.busy} deletingDocumentId={app.deletingDocumentId} documents={app.documents} handleDeleteDocument={app.handleDeleteDocument} handleReindex={app.handleReindex} />} />
                <Route path="/jobs" element={<JobsPage jobs={app.jobs} />} />
                <Route path="/settings" element={<SettingsPage apiUrl={app.apiUrl} health={app.health} />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
              {app.error ? <div className="error">{app.error}</div> : null}
              {app.notice ? <div className={`notice notice-${app.notice.tone}`}>{app.notice.message}</div> : null}
            </AppShell>
          }
        />
      </Routes>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
