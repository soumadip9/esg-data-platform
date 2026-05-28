import { FormEvent, useState } from "react";
import { api } from "../api";

export default function LoginPage() {
  const [username, setUsername] = useState("analyst");
  const [password, setPassword] = useState("demo1234");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { access } = await api.login(username, password);
      localStorage.setItem("access_token", access);
      window.location.href = "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>Breathe ESG</h1>
        <p className="subtitle">Emissions data review platform</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          <button type="submit" className="btn-primary" style={{ width: "100%" }} disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
          {error && <p className="error-msg">{error}</p>}
        </form>
        <p style={{ marginTop: "1rem", fontSize: "0.8rem", color: "var(--text-muted)" }}>
          Demo: analyst / demo1234
        </p>
      </div>
    </div>
  );
}
