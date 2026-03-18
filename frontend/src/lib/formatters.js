export function parseJson(value) {
  return JSON.parse(value);
}

export function buildStats(documents) {
  const indexed = documents.filter((document) => document.status === "indexed").length;
  const stale = documents.filter((document) => document.is_index_stale).length;
  const chunks = documents.reduce((total, document) => total + document.chunk_count, 0);

  return [
    { label: "Documents", value: documents.length },
    { label: "Indexed", value: indexed },
    { label: "Stale", value: stale },
    { label: "Chunks", value: chunks },
  ];
}

export function buildFilterOptions(documents) {
  const countries = new Set();
  const categories = new Set();

  documents.forEach((document) => {
    const metadata = document.metadata_summary || {};
    if (typeof metadata.country === "string" && metadata.country) {
      countries.add(metadata.country);
    }
    const category = firstString(metadata.category, metadata.domain, metadata.type);
    if (category) {
      categories.add(category);
    }
  });

  return {
    countries: Array.from(countries).sort(),
    categories: Array.from(categories).sort(),
  };
}

export function buildQueryFilters(queryForm) {
  const filters = {};

  if (queryForm.country) {
    filters.country = queryForm.country;
  }
  if (queryForm.category) {
    filters.category = queryForm.category;
  }
  if (queryForm.extraFilters) {
    Object.assign(filters, parseJson(queryForm.extraFilters));
  }

  return filters;
}

export function formatDate(value) {
  if (!value) {
    return "n/a";
  }
  return new Date(value).toLocaleDateString();
}

export function formatOptionLabel(value) {
  return value
    .split(/[-_]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function formatBytes(value) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "n/a";
  }
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function firstString(...values) {
  return values.find((value) => typeof value === "string" && value) || "";
}
