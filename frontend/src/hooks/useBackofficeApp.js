import { useEffect, useState } from "react";

import { emptyQuery, retrievalPhases } from "../constants.js";
import { readError, resolveApiUrl } from "../lib/api.js";
import {
  buildFilterOptions,
  buildQueryFilters,
  buildStats,
  parseJson,
} from "../lib/formatters.js";

const apiUrl = resolveApiUrl();

export function useBackofficeApp() {
  const [documents, setDocuments] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [health, setHealth] = useState(null);
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
  const [deletingDocumentId, setDeletingDocumentId] = useState(null);

  useEffect(() => {
    void refreshDocuments();
    void refreshHealth();
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

  async function refreshHealth() {
    const response = await fetch(`${apiUrl}/health`);
    if (!response.ok) {
      return;
    }
    setHealth(await response.json());
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
    try {
      const response = await fetch(`${apiUrl}/documents/${document.id}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      setJobs((currentJobs) => currentJobs.filter((job) => job.document_id !== document.id));
      setQueryResult(null);
      await refreshDocuments();
    } catch (caught) {
      setError(caught.message);
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

  return {
    apiUrl,
    busy,
    deletingDocumentId,
    documents,
    error,
    filterOptions: buildFilterOptions(documents),
    health,
    jobs,
    loadingPhase,
    metadataText,
    payloadText,
    queryBusy,
    queryForm,
    queryResult,
    showAdvanced,
    stats: buildStats(documents),
    setError,
    setMetadataText,
    setPayloadText,
    setQueryForm,
    setShowAdvanced,
    handleDeleteDocument,
    handleFileIngest,
    handlePayloadIngest,
    handleQuery,
    handleReindex,
    refreshDocuments,
    refreshHealth,
  };
}
