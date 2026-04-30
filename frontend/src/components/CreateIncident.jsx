import { useState } from "react";
import { createAlert } from "../api";

export default function CreateIncident({ onRefresh }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ title: "", description: "", severity: "P3", service_affected: "", alert_source: "manual" });
  const [msg, setMsg] = useState("");

  const handle = async () => {
    try {
      await createAlert(form);
      setMsg("Incident created!");
      setForm({ title: "", description: "", severity: "P3", service_affected: "", alert_source: "manual" });
      onRefresh();
      setTimeout(() => { setMsg(""); setOpen(false); }, 1500);
    } catch (e) {
      setMsg(e.response?.data?.detail?.[0]?.msg || "Error creating incident");
    }
  };

  const input = { width: "100%", background: "#13131f", border: "1px solid #333", borderRadius: "6px", padding: "8px 12px", color: "#fff", fontSize: "14px", marginBottom: "12px", boxSizing: "border-box" };

  return (
    <div>
      <button onClick={() => setOpen(!open)} style={{ background: "#6366f1", color: "#fff", border: "none", borderRadius: "8px", padding: "10px 22px", cursor: "pointer", fontWeight: 700, fontSize: "14px" }}>
        + New Incident
      </button>
      {open && (
        <div style={{ background: "#1e1e2e", borderRadius: "10px", padding: "24px", marginTop: "16px" }}>
          <h3 style={{ color: "#fff", marginBottom: "16px" }}>Create New Incident</h3>
          <input placeholder="Title" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} style={input} />
          <textarea placeholder="Description" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={3} style={{ ...input, resize: "vertical" }} />
          <select value={form.severity} onChange={e => setForm({ ...form, severity: e.target.value })} style={input}>
            <option value="P1">P1 — Critical</option>
            <option value="P2">P2 — High</option>
            <option value="P3">P3 — Medium</option>
          </select>
          <input placeholder="Service affected (e.g. payments-api)" value={form.service_affected} onChange={e => setForm({ ...form, service_affected: e.target.value })} style={input} />
          <input placeholder="Alert source (e.g. datadog)" value={form.alert_source} onChange={e => setForm({ ...form, alert_source: e.target.value })} style={input} />
          <button onClick={handle} style={{ background: "#10b981", color: "#fff", border: "none", borderRadius: "6px", padding: "10px 24px", cursor: "pointer", fontWeight: 700 }}>Create</button>
          {msg && <span style={{ marginLeft: "12px", color: "#10b981", fontSize: "13px" }}>{msg}</span>}
        </div>
      )}
    </div>
  );
}
