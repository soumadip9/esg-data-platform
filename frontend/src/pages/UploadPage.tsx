import { useEffect, useRef, useState } from "react";
import { api, IngestionRun } from "../api";

const SOURCE_TYPES = [
  { value: "sap", label: "SAP Procurement (TSV)", accept: ".tsv,.txt,.csv" },
  { value: "utility", label: "Utility Electricity (CSV)", accept: ".csv" },
  { value: "travel", label: "Corporate Travel (Pipe-delimited)", accept: ".txt,.csv" },
];

export default function UploadPage() {
  const [sourceType, setSourceType] = useState("sap");
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [runs, setRuns] = useState<IngestionRun[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  const loadRuns = () => {
    api.ingestionRuns().then((data) => setRuns(data.results));
  };

  useEffect(() => {
    loadRuns();
  }, []);

  const handleUpload = async (file: File) => {
    setUploading(true);
    setMessage("");
    setError("");
    try {
      const run = await api.upload(sourceType, file);
      setMessage(`Upload started: ${run.filename} — status ${run.status_display}`);
      setTimeout(loadRuns, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const currentSource = SOURCE_TYPES.find((s) => s.value === sourceType)!;

  return (
    <>
      <div className="page-header">
        <h1>Data Ingestion</h1>
        <p>Upload source files from SAP, utility portals, or travel platforms</p>
      </div>

      <div className="card">
        <h2>Upload File</h2>
        <div className="form-group" style={{ maxWidth: 400, marginBottom: "1rem" }}>
          <label>Data Source</label>
          <select value={sourceType} onChange={(e) => setSourceType(e.target.value)}>
            {SOURCE_TYPES.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </div>

        <div
          className="upload-zone"
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const file = e.dataTransfer.files[0];
            if (file) handleUpload(file);
          }}
        >
          <input
            ref={fileRef}
            type="file"
            accept={currentSource.accept}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleUpload(file);
            }}
          />
          <p>{uploading ? "Uploading…" : "Drop file here or click to browse"}</p>
          <p style={{ fontSize: "0.8rem", marginTop: "0.5rem" }}>
            Sample files in <code>/sample_data/</code>
          </p>
        </div>
        {message && <p style={{ color: "var(--accent)", marginTop: "1rem" }}>{message}</p>}
        {error && <p className="error-msg">{error}</p>}
      </div>

      <div className="card">
        <h2>Recent Ingestion Runs</h2>
        {runs.length === 0 ? (
          <div className="empty-state">No ingestion runs yet</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>File</th>
                <th>Source</th>
                <th>Status</th>
                <th>Success</th>
                <th>Failed</th>
                <th>Flagged</th>
                <th>Duplicates</th>
                <th>When</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id}>
                  <td>{r.filename}</td>
                  <td>{r.source_type_display}</td>
                  <td>{r.status_display}</td>
                  <td className="mono">{r.rows_success}</td>
                  <td className="mono">{r.rows_failed}</td>
                  <td className="mono">{r.rows_flagged}</td>
                  <td className="mono">{r.rows_duplicate}</td>
                  <td className="mono">{new Date(r.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
