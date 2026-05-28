import { FormEvent, useCallback, useEffect, useState } from "react";
import { api, Activity, AuditLogEntry } from "../api";

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

const ACTION_LABELS: Record<string, string> = {
  created: "Record created",
  updated: "Record updated",
  flagged: "Flagged for review",
  approved: "Approved by analyst",
  locked: "Locked for audit",
  edited: "Edited by analyst",
};

function scopeClass(scope: string) {
  if (scope.includes("1")) return "scope-1";
  if (scope.includes("2")) return "scope-2";
  return "scope-3";
}

function formatDetails(details: Record<string, unknown>) {
  if (!details || Object.keys(details).length === 0) return "—";
  try {
    return JSON.stringify(details, null, 2);
  } catch {
    return String(details);
  }
}

interface EditForm {
  quantity: string;
  unit: string;
  description: string;
  site_name: string;
  analyst_notes: string;
}

function toEditForm(a: Activity): EditForm {
  return {
    quantity: String(a.quantity),
    unit: a.unit,
    description: a.description,
    site_name: a.site_name,
    analyst_notes: a.analyst_notes,
  };
}

export default function ReviewPage() {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [statusFilter, setStatusFilter] = useState("flagged");
  const [sourceFilter, setSourceFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const [detailActivity, setDetailActivity] = useState<Activity | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [auditLoading, setAuditLoading] = useState(false);

  const [editActivity, setEditActivity] = useState<Activity | null>(null);
  const [editForm, setEditForm] = useState<EditForm | null>(null);
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState("");

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

  const openAuditPanel = async (activity: Activity) => {
    setDetailActivity(activity);
    setAuditLoading(true);
    try {
      const logs = await api.activityAuditLogs(activity.id);
      setAuditLogs(logs);
    } catch {
      setAuditLogs([]);
    } finally {
      setAuditLoading(false);
    }
  };

  const closeAuditPanel = () => {
    setDetailActivity(null);
    setAuditLogs([]);
  };

  const openEditModal = (activity: Activity) => {
    setEditActivity(activity);
    setEditForm(toEditForm(activity));
    setEditError("");
  };

  const closeEditModal = () => {
    setEditActivity(null);
    setEditForm(null);
    setEditError("");
  };

  const handleEditSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!editActivity || !editForm) return;
    setEditSaving(true);
    setEditError("");
    try {
      const updated = await api.editActivity(editActivity.id, {
        quantity: editForm.quantity,
        unit: editForm.unit,
        description: editForm.description,
        site_name: editForm.site_name,
        analyst_notes: editForm.analyst_notes,
      });
      closeEditModal();
      await load();
      if (detailActivity?.id === editActivity.id) {
        await openAuditPanel(updated);
      }
    } catch (err) {
      setEditError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setEditSaving(false);
    }
  };

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
      if (detailActivity && selected.has(detailActivity.id)) {
        closeAuditPanel();
      }
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

      <div className={`review-layout${detailActivity ? " with-panel" : ""}`}>
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
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {activities.map((a) => (
                  <tr key={a.id} className={detailActivity?.id === a.id ? "row-active" : ""}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selected.has(a.id)}
                        onChange={() => toggleSelect(a.id)}
                      />
                    </td>
                    <td>
                      <span className={`badge badge-${a.status}`}>{a.status_display}</span>
                      {a.is_edited && (
                        <span className="badge badge-edited" title="Analyst edited">Edited</span>
                      )}
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
                      <div className="mono muted-sm">{a.source_reference}</div>
                    </td>
                    <td className="mono">
                      {Number(a.quantity).toLocaleString()} {a.unit}
                      {a.original_unit && a.original_unit !== a.unit && (
                        <div className="muted-sm">
                          was {Number(a.original_quantity).toLocaleString()} {a.original_unit}
                        </div>
                      )}
                    </td>
                    <td>{a.site_name || a.site_code || "—"}</td>
                    <td className="flag-reason">{a.flag_reason || "—"}</td>
                    <td className="actions-col">
                      <button className="btn-secondary btn-sm" onClick={() => openAuditPanel(a)}>
                        History
                      </button>
                      <button
                        className="btn-secondary btn-sm"
                        disabled={a.status === "locked"}
                        onClick={() => openEditModal(a)}
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {detailActivity && (
          <div className="card audit-panel">
            <div className="panel-header">
              <h2>Audit Trail</h2>
              <button className="btn-secondary btn-sm" onClick={closeAuditPanel}>Close</button>
            </div>
            <div className="panel-meta">
              <div><strong>{detailActivity.description || detailActivity.category_display}</strong></div>
              <div className="mono muted-sm">{detailActivity.source_reference}</div>
              <div className="muted-sm">
                Status: {detailActivity.status_display}
                {detailActivity.reviewed_by_name && (
                  <> · Reviewed by {detailActivity.reviewed_by_name}</>
                )}
              </div>
            </div>
            {auditLoading ? (
              <p>Loading audit log…</p>
            ) : auditLogs.length === 0 ? (
              <p className="muted-sm">No audit entries yet.</p>
            ) : (
              <ul className="audit-list">
                {auditLogs.map((log) => (
                  <li key={log.id} className="audit-item">
                    <div className="audit-item-header">
                      <span className="audit-action">{ACTION_LABELS[log.action] || log.action}</span>
                      <span className="mono muted-sm">
                        {new Date(log.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="muted-sm">By: {log.actor_name || "System"}</div>
                    {Object.keys(log.details).length > 0 && (
                      <pre className="audit-details">{formatDetails(log.details)}</pre>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      {editActivity && editForm && (
        <div className="modal-overlay" onClick={closeEditModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="panel-header">
              <h2>Edit Activity</h2>
              <button className="btn-secondary btn-sm" onClick={closeEditModal}>Cancel</button>
            </div>
            <p className="muted-sm modal-subtitle">
              {editActivity.source_reference} · {editActivity.category_display}
              {editActivity.status === "locked" && (
                <span className="error-msg"> Locked records cannot be edited.</span>
              )}
            </p>
            <form onSubmit={handleEditSubmit}>
              <div className="form-row">
                <div className="form-group">
                  <label>Quantity</label>
                  <input
                    value={editForm.quantity}
                    onChange={(e) => setEditForm({ ...editForm, quantity: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Unit</label>
                  <input
                    value={editForm.unit}
                    onChange={(e) => setEditForm({ ...editForm, unit: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Description</label>
                <input
                  value={editForm.description}
                  onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Site name</label>
                <input
                  value={editForm.site_name}
                  onChange={(e) => setEditForm({ ...editForm, site_name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Analyst notes</label>
                <textarea
                  rows={3}
                  value={editForm.analyst_notes}
                  onChange={(e) => setEditForm({ ...editForm, analyst_notes: e.target.value })}
                />
              </div>
              {editError && <p className="error-msg">{editError}</p>}
              <div className="modal-actions">
                <button type="submit" className="btn-primary" disabled={editSaving}>
                  {editSaving ? "Saving…" : "Save changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
