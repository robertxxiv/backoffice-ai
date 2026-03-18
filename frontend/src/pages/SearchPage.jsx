import { exampleQuestions } from "../constants.js";
import { formatOptionLabel } from "../lib/formatters.js";
import { MarkdownAnswer, QueryLoadingState } from "../components/QueryWidgets.jsx";

export function SearchPage({
  busy,
  filterOptions,
  handleQuery,
  loadingPhase,
  queryBusy,
  queryForm,
  queryResult,
  setQueryForm,
  setShowAdvanced,
  showAdvanced,
}) {
  return (
    <div className="page-stack">
      <section className="card section-card page-header-card">
        <div className="section-intro compact">
          <p className="section-label">Search</p>
          <h2>Run a grounded query</h2>
          <p>Search indexed knowledge, inspect evidence, and keep advanced retrieval controls secondary.</p>
        </div>
      </section>

      <section className="card section-card">
        <div className="prompt-suggestions">
          {exampleQuestions.map((question) => (
            <button
              key={question}
              className="suggestion-chip"
              onClick={() => setQueryForm({ ...queryForm, query: question })}
              type="button"
            >
              {question}
            </button>
          ))}
        </div>
        <form onSubmit={handleQuery} className="query-form">
          <label className="query-query">
            <span className="field-label">Ask your question</span>
            <input
              type="text"
              placeholder="Ask about uploaded and indexed documents…"
              value={queryForm.query}
              onChange={(event) => setQueryForm({ ...queryForm, query: event.target.value })}
            />
          </label>
          <label>
            <span className="field-label">Category</span>
            <select
              value={queryForm.category}
              onChange={(event) => setQueryForm({ ...queryForm, category: event.target.value })}
            >
              <option value="">All categories</option>
              {filterOptions.categories.map((category) => (
                <option key={category} value={category}>
                  {formatOptionLabel(category)}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span className="field-label">Country</span>
            <select
              value={queryForm.country}
              onChange={(event) => setQueryForm({ ...queryForm, country: event.target.value })}
            >
              <option value="">Any country</option>
              {filterOptions.countries.map((country) => (
                <option key={country} value={country}>
                  {country}
                </option>
              ))}
            </select>
          </label>
          <button className="primary-button" disabled={busy} type="submit">
            Search
          </button>
        </form>
        <div className="query-help">
          <p>Queries run only against indexed documents. Upload then reindex first.</p>
          <button
            className="link-button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            type="button"
          >
            {showAdvanced ? "Hide advanced" : "Advanced options"}
          </button>
        </div>

        {showAdvanced ? (
          <div className="advanced-panel">
            <div className="advanced-grid">
              <label>
                <span className="field-label">Retrieval breadth</span>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={queryForm.top_k}
                  onChange={(event) => setQueryForm({ ...queryForm, top_k: event.target.value })}
                />
              </label>
              <label>
                <span className="field-label">Extra filters JSON</span>
                <input
                  type="text"
                  placeholder='{"customer":"hertz"}'
                  value={queryForm.extraFilters}
                  onChange={(event) => setQueryForm({ ...queryForm, extraFilters: event.target.value })}
                />
              </label>
            </div>
          </div>
        ) : null}

        {queryBusy ? <QueryLoadingState activeIndex={loadingPhase} /> : null}

        {queryResult && !queryBusy ? (
          <div className="result">
            <div className="result-block">
              <p className="section-label">Answer</p>
              <MarkdownAnswer text={queryResult.answer} />
            </div>

            {queryResult.machine_output ? (
              <details className="machine-panel">
                <summary>▸ Show structured data</summary>
                <pre>{JSON.stringify(queryResult.machine_output, null, 2)}</pre>
              </details>
            ) : null}

            <div className="result-block">
              <p className="section-label">
                Sources
                {queryResult.sources.length > 0 ? (
                  <span style={{ marginLeft: "0.5rem", fontFamily: "var(--font-mono)", fontSize: "0.75rem", letterSpacing: 0, textTransform: "none", color: "var(--text-muted)", fontWeight: 400 }}>
                    ({queryResult.sources.length})
                  </span>
                ) : null}
              </p>
            </div>
            <div className="list">
              {queryResult.sources.map((source) => (
                <article key={source.chunk} className="source">
                  <div className="item-title-row">
                    <strong style={{ fontSize: "0.9rem" }}>{source.document}</strong>
                    <span className="score-pill">{Number(source.score).toFixed(3)}</span>
                  </div>
                  <p>{source.excerpt}</p>
                  <small>chunk evidence · relevance {Number(source.score).toFixed(3)}</small>
                </article>
              ))}
            </div>

            <details className="trace-panel">
              <summary>▸ Show technical details</summary>
              <pre>{JSON.stringify(queryResult.trace, null, 2)}</pre>
            </details>
          </div>
        ) : null}
      </section>
    </div>
  );
}
