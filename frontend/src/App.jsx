import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";

import { AppShell } from "./components/AppShell.jsx";
import { useBackofficeApp } from "./hooks/useBackofficeApp.js";
import { DashboardPage } from "./pages/DashboardPage.jsx";
import { DocumentsPage } from "./pages/DocumentsPage.jsx";
import { IngestionPage } from "./pages/IngestionPage.jsx";
import { JobsPage } from "./pages/JobsPage.jsx";
import { LandingPage } from "./pages/LandingPage.jsx";
import { LoginPage } from "./pages/LoginPage.jsx";
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

  if (!app.authReady) {
    return <div className="app-loading">Loading workspace…</div>;
  }

  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<LandingPage currentUser={app.currentUser} stats={app.stats} />} />
        <Route
          path="/login"
          element={
            app.currentUser ? (
              <Navigate to="/dashboard" replace />
            ) : (
              <LoginPage
                busy={app.busy}
                error={app.error}
                handleLogin={app.handleLogin}
                loginForm={app.loginForm}
                setLoginForm={app.setLoginForm}
              />
            )
          }
        />

        <Route
          path="/*"
          element={
            app.currentUser ? (
              <AppShell currentUser={app.currentUser} onLogout={app.handleLogout}>
                <Routes>
                  <Route path="/dashboard" element={<DashboardPage stats={app.stats} documents={app.documents} jobs={app.jobs} isAdmin={app.isAdmin} />} />
                  <Route path="/ingestion" element={<IngestionPage {...app} />} />
                  <Route path="/search" element={<SearchPage {...app} />} />
                  <Route path="/documents" element={<DocumentsPage busy={app.busy} deletingDocumentId={app.deletingDocumentId} documents={app.documents} handleDeleteDocument={app.handleDeleteDocument} handleReindex={app.handleReindex} isAdmin={app.isAdmin} />} />
                  <Route path="/jobs" element={app.isAdmin ? <JobsPage jobs={app.jobs} /> : <Navigate to="/dashboard" replace />} />
                  <Route
                    path="/settings"
                    element={app.isAdmin ? (
                      <SettingsPage
                        apiUrl={app.apiUrl}
                        currentUser={app.currentUser}
                        handleCreateUser={app.handleCreateUser}
                        health={app.health}
                        setUserForm={app.setUserForm}
                        userForm={app.userForm}
                        users={app.users}
                      />
                    ) : <Navigate to="/dashboard" replace />}
                  />
                  <Route path="*" element={<Navigate to="/dashboard" replace />} />
                </Routes>
                {app.error ? <div className="error">{app.error}</div> : null}
                {app.notice ? <div className={`notice notice-${app.notice.tone}`}>{app.notice.message}</div> : null}
              </AppShell>
            ) : (
              <Navigate to="/login" replace />
            )
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
