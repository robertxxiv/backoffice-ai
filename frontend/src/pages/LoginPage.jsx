import { Link } from "react-router-dom";


export function LoginPage({ busy, error, handleLogin, loginForm, setLoginForm }) {
  return (
    <div className="landing auth-landing">
      <div className="landing-bg-orbit landing-orbit-a" />
      <div className="landing-bg-orbit landing-orbit-b" />

      <div className="landing-content auth-content">
        <section className="auth-card">
          <div className="landing-badge">
            <span className="landing-badge-dot" />
            Secure Workspace Access
          </div>
          <h1 className="landing-title">
            Backoffice<span className="landing-title-accent">.AI</span>
          </h1>
          <p className="landing-subtitle">
            Sign in to ingest documents, query the indexed knowledge base, and manage the shared workspace.
          </p>

          <form className="stack" onSubmit={handleLogin}>
            <label>
              <span className="field-label">Email</span>
              <input
                type="text"
                value={loginForm.email}
                onChange={(event) => setLoginForm({ ...loginForm, email: event.target.value })}
              />
            </label>
            <label>
              <span className="field-label">Password</span>
              <input
                type="password"
                value={loginForm.password}
                onChange={(event) => setLoginForm({ ...loginForm, password: event.target.value })}
              />
            </label>
            <button className="primary-button" disabled={busy} type="submit">
              Sign in
            </button>
          </form>

          {error ? <div className="error auth-error">{error}</div> : null}

          <p className="panel-note">
            Need the public overview instead? <Link to="/">Go back to the landing page</Link>.
          </p>
        </section>
      </div>
    </div>
  );
}
