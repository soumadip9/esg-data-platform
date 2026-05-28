import { useCallback, useEffect, useState } from "react";
import { api, Activity } from "../api";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "pending", label: "Pending" },
  { value: "flagged", label: "Flagged" },
  { value: "approved", label: "Approved" },
  { value: "locked", label: "Locked" },
];

const SOURCE_OPTIONS = [
  { value: "", label: "All sources" },
  { value: "sap", label: "SAP" },
  { value: "utility", label: "Utility" },
  { value: "travel", label: "Travel" },
];

function scopeClass(scope: string) {
  if (scope.includes("1")) return "scope-1";
  if (scope.includes("2")) return "scope-2";
  return "scope-3";
}

export default function ReviewPage() {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [statusFilter, setStatusFilter] = useState("flagged");
  const [sourceFilter, setSourceFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const params: Record<string, string> = { ordering: "-activity_date" };
    if (statusFilter) params.status = statusFilter;
    if (sourceFilter) params.source_type = sourceFilter;
    const data = await api.activities(params);
    setActivities(data.results);
    setSelected(new Set());
    setLoading(false);
  }, [statusFilter, sourceFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selected.size === activities.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(activities.map((a) => a.id)));
    }
  };

  const handleBulk = async (action: string) => {
    if (selected.size === 0) return;
    setActionLoading(true);
    try {
      await api.bulkReview([...selected], action);
      await load();
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <>
      <div className="page-header">
        <h1>Review Queue</h1>
        <p>Inspect ingested rows, resolve flags, and approve data for audit lock</p>
      </div>

      <div className="toolbar">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)}>
          {SOURCE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <button
          className="btn-primary btn-sm"
          disabled={selected.size === 0 || actionLoading}
          onClick={() => handleBulk("approve")}
        >
          Approve selected ({selected.size})
        </button>
        <button
          className="btn-secondary btn-sm"
          disabled={selected.size === 0 || actionLoading}
          onClick={() => handleBulk("flag")}
        >
          Flag selected
        </button>
        <button
          className="btn-secondary btn-sm"
          disabled={selected.size === 0 || actionLoading}
          onClick={() => handleBulk("lock")}
        >
          Lock approved
        </button>
      </div>

      <div className="card">
        {loading ? (
          <p>Loading…</p>
        ) : activities.length === 0 ? (
          <div className="empty-state">No records match your filters</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th className="checkbox-col">
                  <input
                    type="checkbox"
                    checked={selected.size === activities.length && activities.length > 0}
                    onChange={toggleAll}
                  />
                </th>
                <th>Status</th>
                <th>Source</th>
                <th>Scope</th>
                <th>Date</th>
                <th>Description</th>
                <th>Quantity</th>
                <th>Site</th>
                <th>Flags</th>
              </tr>
            </thead>
            <tbody>
              {activities.map((a) => (
                <tr key={a.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selected.has(a.id)}
                      onChange={() => toggleSelect(a.id)}
                    />
                  </td>
                  <td>
                    <span className={`badge badge-${a.status}`}>{a.status_display}</span>
                  </td>
                  <td>{a.source_type_display}</td>
                  <td>
                    <span className={`scope-badge ${scopeClass(a.scope)}`}>
                      {a.scope.replace("scope_", "S")}
                    </span>
                  </td>
                  <td className="mono">{a.activity_date}</td>
                  <td>
                    <div>{a.description || a.category_display}</div>
                    <div className="mono" style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                      {a.source_reference}
                    </div>
                  </td>
                  <td className="mono">
                    {Number(a.quantity).toLocaleString()} {a.unit}
                    {a.original_unit && a.original_unit !== a.unit && (
                      <div style={{ color: "var(--text-muted)", fontSize: "0.75rem" }}>
                        was {Number(a.original_quantity).toLocaleString()} {a.original_unit}
                      </div>
                    )}
                  </td>
                  <td>{a.site_name || a.site_code || "—"}</td>
                  <td className="flag-reason">{a.flag_reason || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
