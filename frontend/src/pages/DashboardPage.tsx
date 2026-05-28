import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, DashboardStats } from "../api";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.dashboard().then(setStats).finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading dashboard…</p>;
  if (!stats) return <p>Failed to load dashboard</p>;

  const sourceLabels: Record<string, string> = {
    sap: "SAP Procurement",
    utility: "Utility Electricity",
    travel: "Corporate Travel",
  };

  return (
    <>
      <div className="page-header">
        <h1>Review Dashboard</h1>
        <p>Overview of ingested emissions activity data awaiting analyst sign-off</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="label">Total Records</div>
          <div className="value">{stats.total}</div>
        </div>
        <div className="stat-card pending">
          <div className="label">Pending Review</div>
          <div className="value">{stats.pending}</div>
        </div>
        <div className="stat-card flagged">
          <div className="label">Flagged</div>
          <div className="value">{stats.flagged}</div>
        </div>
        <div className="stat-card approved">
          <div className="label">Approved</div>
          <div className="value">{stats.approved}</div>
        </div>
        <div className="stat-card locked">
          <div className="label">Locked for Audit</div>
          <div className="value">{stats.locked}</div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
        <div className="card">
          <h2>By Data Source</h2>
          <table>
            <tbody>
              {Object.entries(stats.by_source).map(([key, count]) => (
                <tr key={key}>
                  <td>{sourceLabels[key] || key}</td>
                  <td className="mono">{count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card">
          <h2>By GHG Scope</h2>
          <table>
            <tbody>
              {Object.entries(stats.by_scope).map(([key, count]) => (
                <tr key={key}>
                  <td>{key.replace("_", " ").replace("scope", "Scope ")}</td>
                  <td className="mono">{count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {(stats.pending > 0 || stats.flagged > 0) && (
        <div className="card" style={{ marginTop: "1rem" }}>
          <h2>Action Required</h2>
          <p style={{ color: "var(--text-muted)", marginBottom: "1rem" }}>
            {stats.flagged} records flagged for review, {stats.pending} pending initial review.
          </p>
          <Link to="/review" className="btn-primary" style={{ display: "inline-block", padding: "0.5rem 1rem" }}>
            Go to Review Queue →
          </Link>
        </div>
      )}
    </>
  );
}
