import ReactMarkdown from "react-markdown";

import { retrievalPhases } from "../constants.js";

export function QueryLoadingState({ activeIndex }) {
  return (
    <div className="loading-panel" aria-live="polite" aria-busy="true">
      <div className="loading-head">
        <p className="section-label">Working</p>
        <h3>Building your answer</h3>
      </div>
      <div className="loading-phase-list">
        {retrievalPhases.map((phase, index) => {
          const state = index < activeIndex ? "complete" : index === activeIndex ? "active" : "idle";

          return (
            <article key={phase.label} className={`loading-phase phase-${state}`}>
              <div className="phase-marker">
                <span />
              </div>
              <div className="phase-copy">
                <strong>{phase.label}</strong>
                <p>{phase.detail}</p>
                <div className="phase-skeletons" aria-hidden="true">
                  <span className="skeleton-line short" />
                  <span className="skeleton-line medium" />
                  <span className="skeleton-line long" />
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}

export function MarkdownAnswer({ text }) {
  return (
    <div className="answer-markdown">
      <ReactMarkdown components={markdownComponents}>{text}</ReactMarkdown>
    </div>
  );
}

const markdownComponents = {
  h1: ({ children }) => <h1 className="markdown-h1">{children}</h1>,
  h2: ({ children }) => <h2 className="markdown-h2">{children}</h2>,
  h3: ({ children }) => <h3 className="markdown-h3">{children}</h3>,
  p: ({ children }) => <p className="answer-paragraph">{children}</p>,
  ul: ({ children }) => <ul className="answer-list">{children}</ul>,
  li: ({ children }) => <li>{children}</li>,
  code: ({ inline, children }) =>
    inline ? (
      <code className="inline-code">{children}</code>
    ) : (
      <code className="code-block">{children}</code>
    ),
  pre: ({ children }) => <pre className="markdown-pre">{children}</pre>,
  strong: ({ children }) => <strong className="markdown-strong">{children}</strong>,
};
