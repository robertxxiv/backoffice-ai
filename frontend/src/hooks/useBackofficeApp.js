import { useEffect, useMemo, useState } from "react";

import { emptyQuery, retrievalPhases } from "../constants.js";
import { authHeaders, getStoredToken, readError, resolveApiUrl, storeToken } from "../lib/api.js";
import {
  buildFilterOptions,
  buildQueryFilters,
  buildStats,
  parseJson,
} from "../lib/formatters.js";

const apiUrl = resolveApiUrl();

export function useBackofficeApp() {
  const [accessToken, setAccessToken] = useState(getStoredToken());
  const [authReady, setAuthReady] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [health, setHealth] = useState(null);
  const [payloadText, setPayloadText] = useState(
    "Norwegian VAT for consulting is 25 percent. Winter season pricing applies from December to February.",
  );
  const [metadataText, setMetadataText] = useState('{"country":"NO","domain":"quotes"}');
  const [queryForm, setQueryForm] = useState(emptyQuery);
  const [queryResult, setQueryResult] = useState(null);
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [userForm, setUserForm] = useState({ email: "", password: "", role: "user" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState(null);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [queryBusy, setQueryBusy] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState(0);
  const [deletingDocumentId, setDeletingDocumentId] = useState(null);

  const isAdmin = currentUser?.role === "admin";

  useEffect(() => {
    void refreshHealth();
  }, []);

  useEffect(() => {
    if (!accessToken) {
      clearSessionState(false);
      setAuthReady(true);
      return;
    }

    let active = true;
    void (async () => {
      try {
        const response = await fetch(`${apiUrl}/auth/me`, {
          headers: authHeaders(accessToken),
        });
        if (!response.ok) {
          throw new Error(await readError(response));
        }
        const payload = await response.json();
        if (!active) {
          return;
        }
        setCurrentUser(payload);
        await refreshDocuments(accessToken);
        if (payload.role === "admin") {
          await refreshUsers(accessToken, true);
        } else {
          setUsers([]);
        }
      } catch {
        storeToken("");
        if (!active) {
          return;
        }
        clearSessionState(false);
      } finally {
        if (active) {
          setAuthReady(true);
        }
      }
    })();

    return () => {
      active = false;
    };
  }, [accessToken]);

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

  useEffect(() => {
    if (!notice) {
      return undefined;
    }
    const timer = window.setTimeout(() => setNotice(null), 5000);
    return () => window.clearTimeout(timer);
  }, [notice]);

  const filterOptions = useMemo(() => buildFilterOptions(documents), [documents]);
  const stats = useMemo(() => buildStats(documents), [documents]);

  async function apiRequest(path, options = {}, requestOptions = {}) {
    const { requireAuth = true } = requestOptions;
    const headers = requireAuth
      ? authHeaders(accessToken, options.headers || {})
      : (options.headers || {});
    const response = await fetch(`${apiUrl}${path}`, { ...options, headers });
    if (response.status === 401 && requireAuth) {
      handleLogout(false);
      throw new Error("Your session has expired. Please sign in again.");
    }
    return response;
  }

  function clearSessionState(clearToken = true) {
    if (clearToken) {
      setAccessToken("");
      storeToken("");
    }
    setCurrentUser(null);
    setUsers([]);
    setDocuments([]);
    setJobs([]);
    setQueryResult(null);
  }

  async function refreshDocuments(token = accessToken) {
    if (!token) {
      setDocuments([]);
      return;
    }
    const response = await fetch(`${apiUrl}/documents`, { headers: authHeaders(token) });
    if (!response.ok) {
      throw new Error(await readError(response));
    }
    setDocuments(await response.json());
  }

  async function refreshUsers(token = accessToken, allow = isAdmin) {
    if (!token || !allow) {
      setUsers([]);
      return;
    }
    const response = await fetch(`${apiUrl}/auth/users`, { headers: authHeaders(token) });
    if (!response.ok) {
      throw new Error(await readError(response));
    }
    setUsers(await response.json());
  }

  async function refreshHealth() {
    const response = await fetch(`${apiUrl}/health`);
    if (!response.ok) {
      return;
    }
    setHealth(await response.json());
  }

  async function handleLogin(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const response = await apiRequest(
        "/auth/login",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(loginForm),
        },
        { requireAuth: false },
      );
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      const payload = await response.json();
      storeToken(payload.access_token);
      setAccessToken(payload.access_token);
      setCurrentUser(payload.user);
      setNotice({ tone: "success", message: `Signed in as ${payload.user.email}.` });
      setLoginForm({ email: payload.user.email, password: "" });
    } catch (caught) {
      setError(caught.message);
      setNotice(null);
    } finally {
      setBusy(false);
      setAuthReady(true);
    }
  }

  function handleLogout(showNotice = true) {
    clearSessionState(true);
    setLoginForm({ email: "", password: "" });
    if (showNotice) {
      setNotice({ tone: "success", message: "Signed out successfully." });
    }
  }

  async function handleCreateUser(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice(null);
    try {
      const response = await apiRequest("/auth/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(userForm),
      });
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      await refreshUsers();
      setUserForm({ email: "", password: "", role: "user" });
      setNotice({ tone: "success", message: "User account created successfully." });
    } catch (caught) {
      setError(caught.message);
    } finally {
      setBusy(false);
    }
  }

  async function handlePayloadIngest(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice(null);
    try {
      const response = await apiRequest("/ingest", {
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
      const payload = await response.json();
      setNotice({
        tone: "success",
        message: buildIngestNotice(payload),
      });
      await refreshDocuments();
    } catch (caught) {
      setError(caught.message);
      setNotice(null);
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
    setNotice(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("metadata", metadataText);
      const response = await apiRequest("/ingest", {
        method: "POST",
        body: formData,
      });
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      const payload = await response.json();
      setNotice({
        tone: "success",
        message: buildIngestNotice(payload),
      });
      await refreshDocuments();
      event.target.value = "";
    } catch (caught) {
      setError(caught.message);
      setNotice(null);
    } finally {
      setBusy(false);
    }
  }

  async function handleReindex(documentId = null) {
    setBusy(true);
    setError("");
    setNotice(null);
    try {
      const response = await apiRequest("/reindex", {
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
      setNotice({
        tone: "success",
        message: buildReindexNotice(payload.jobs),
      });
      await refreshDocuments();
    } catch (caught) {
      setError(caught.message);
      setNotice(null);
    } finally {
      setBusy(false);
    }
  }

  async function handleDeleteDocument(document) {
    const confirmed = window.confirm(
      `Delete "${document.source_ref}" from the RAG index? This removes the document, chunks, embeddings, and related indexing jobs.`,
    );
    if (!confirmed) {
      return;
    }
    setBusy(true);
    setDeletingDocumentId(document.id);
    setError("");
    setNotice(null);
    try {
      const response = await apiRequest(`/documents/${document.id}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      setJobs((currentJobs) => currentJobs.filter((job) => job.document_id !== document.id));
      setQueryResult(null);
      setNotice({
        tone: "success",
        message: `Deleted "${document.source_ref}" from the indexed corpus.`,
      });
      await refreshDocuments();
    } catch (caught) {
      setError(caught.message);
      setNotice(null);
    } finally {
      setDeletingDocumentId(null);
      setBusy(false);
    }
  }

  async function handleQuery(event) {
    event.preventDefault();
    setBusy(true);
    setQueryBusy(true);
    setError("");
    setNotice(null);
    setQueryResult(null);
    try {
      const response = await apiRequest("/query", {
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
      setQueryResult(await response.json());
    } catch (caught) {
      setError(caught.message);
    } finally {
      setQueryBusy(false);
      setBusy(false);
    }
  }

  return {
    apiUrl,
    authReady,
    busy,
    currentUser,
    deletingDocumentId,
    documents,
    error,
    filterOptions,
    handleCreateUser,
    handleDeleteDocument,
    handleFileIngest,
    handleLogin,
    handleLogout,
    handlePayloadIngest,
    handleQuery,
    handleReindex,
    health,
    isAdmin,
    jobs,
    loadingPhase,
    loginForm,
    metadataText,
    notice,
    payloadText,
    queryBusy,
    queryForm,
    queryResult,
    refreshDocuments,
    refreshHealth,
    setError,
    setLoginForm,
    setMetadataText,
    setNotice,
    setPayloadText,
    setQueryForm,
    setShowAdvanced,
    setUserForm,
    showAdvanced,
    stats,
    userForm,
    users,
  };
}

function buildIngestNotice(payload) {
  const actionLabel = payload.lifecycle_action === "updated"
    ? "updated"
    : payload.lifecycle_action === "unchanged"
      ? "checked"
      : "ingested";
  const staleHint = payload.is_index_stale ? " Reindex it to make it searchable." : "";
  return `${payload.source_ref} ${actionLabel} successfully.${staleHint}`;
}

function buildReindexNotice(jobs) {
  if (!jobs?.length) {
    return "Reindex request completed.";
  }
  if (jobs.length === 1) {
    return jobs[0].status === "completed"
      ? "Document reindexed successfully."
      : `Reindex job created with status: ${jobs[0].status}.`;
  }
  const completed = jobs.filter((job) => job.status === "completed").length;
  return `${completed} of ${jobs.length} document jobs completed successfully.`;
}
