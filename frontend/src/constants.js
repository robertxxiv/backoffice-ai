export const emptyQuery = {
  query: "",
  top_k: 5,
  country: "",
  category: "",
  extraFilters: "",
};

export const exampleQuestions = [
  "What VAT rule applies to the latest Norwegian invoice?",
  "Summarize the main information in the uploaded quote.",
  "Which document mentions Hertz?",
];

export const retrievalPhases = [
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

export const navItems = [
  { path: "/dashboard", label: "Dashboard" },
  { path: "/ingestion", label: "Ingestion" },
  { path: "/search", label: "Search" },
  { path: "/documents", label: "Documents" },
  { path: "/jobs", label: "Jobs", adminOnly: true },
  { path: "/settings", label: "Settings", adminOnly: true },
];
