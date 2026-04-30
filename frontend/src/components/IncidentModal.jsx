import { useState } from "react";
import { updateStatus, submitRCA } from "../api";

export default function IncidentModal({ incident, onClose, onRefresh }) {
  const [assignee, setAssignee] = useState(incident.assigned_to || "");
  const [rca, setRca] = useState({ root_cause: "", timeline: "", fix_applied: "", prevention: "", written_by: "" });
  const [msg, setMsg] = useState("");

  const handleTransition = async (newStatus) => {
    try {
      await updateStatus(incident.id, { status: newStatus, assigned_to: assignee || undefined });
      setMsg(`Status updated to ${newStatus}`);
      onRefresh();
    } catch (e) {
      setMsg(e.response?.data?.detail || "Error updating status");
    }
  };

  const handleAssign = async () => {
    try {
      await updateStatus(incident.id, { assigned_to: assignee });
      setMsg("Assigned successfully");
      onRefresh();
    } catch (e) {
      setMsg("Error assigning");
    }
  };

  const handleRCA = async () => {
    try {
      await submitRCA(incident.id, rca);
      setMsg("RCA submitted successfully!");
      onRefresh();
    } catch (e) {
      setMsg(e.response?.data?.detail || "Error submitting RCA");
    }
  };

  const overlay = { position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.7)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 };
  const modal = { background: "#1e1e2e", borderRadius: "12px", padding: "32px", width: "620px", maxHeight: "85vh", overflowY: "auto", position: "relative" };
  const input = { width: "100%", background: "#13131f", border: "1px solid #333", borderRadius: "6px", padding: "8px 12px", color: "#fff", fontSize: "14px", marginBottom: "10px", boxSizing: "border-box" };
  const btn = (color) => ({ background: color, color: "#fff", border: "none", borderRadius: "6px", padding: "8px 18px", cursor: "pointer", fontSize: "13px", fontWeight: 600, marginRight: "8px" });

  return (
    <div style={overlay} onClick={onClose}>
      <div style={modal} onClick={e => e.stopPropagation()}>
        <button onClick={onClose} style={{ position: "absolute", top: 16, right: 16, background: "none", border: "none", color: "#888", fontSize: "20px", cursor: "pointer" }}>✕</button>
        <h2 style={{ color: "#fff", marginBottom: "4px" }}>{incident.title}</h2>
        <p style={{ color: "#888", fontSize: "13px", marginBottom: "16px" }}>ID: {incident.id}</p>
        <p style={{ color: "#ccc", marginBottom: "16px" }}>{incident.description}</p>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "20px" }}>
          {[["Severity", incident.severity], ["Status", incident.status], ["Service", incident.service_affected], ["Source", incident.alert_source]].map(([k, v]) => (
            <div key={k} style={{ background: "#13131f", borderRadius: "6px", padding: "10px 14px" }}>
              <div style={{ color: "#666", fontSize: "11px" }}>{k}</div>
              <div style={{ color: "#fff", fontWeight: 600 }}>{v}</div>
            </div>
          ))}
        </div>

        <div style={{ marginBottom: "20px" }}>
          <label style={{ color: "#888", fontSize: "13px" }}>Assign To</label>
          <div style={{ display: "flex", gap: "8px", marginTop: "6px" }}>
            <input value={assignee} onChange={e => setAssignee(e.target.value)} placeholder="Engineer name" style={{ ...input, marginBottom: 0, flex: 1 }} />
            <button onClick={handleAssign} style={btn("#6366f1")}>Assign</button>
          </div>
        </div>

        {incident.allowed_transitions?.length > 0 && (
          <div style={{ marginBottom: "20px" }}>
            <label style={{ color: "#888", fontSize: "13px" }}>Move Status To</label>
            <div style={{ marginTop: "8px" }}>
              {incident.allowed_transitions.map(t => (
                <button key={t} onClick={() => handleTransition(t)} style={btn(t === "closed" ? "#6b7280" : t === "resolved" ? "#10b981" : "#f59e0b")}>{t.toUpperCase()}</button>
              ))}
            </div>
          </div>
        )}

        {!incident.rca && (
          <div style={{ borderTop: "1px solid #333", paddingTop: "20px", marginTop: "8px" }}>
            <h3 style={{ color: "#fff", marginBottom: "14px" }}>Submit RCA Report</h3>
            {["root_cause", "timeline", "fix_applied", "prevention", "written_by"].map(field => (
              <div key={field}>
                <label style={{ color: "#888", fontSize: "12px" }}>{field.replace("_", " ").toUpperCase()}</label>
                {field === "written_by"
                  ? <input value={rca[field]} onChange={e => setRca({ ...rca, [field]: e.target.value })} style={input} placeholder="Your name" />
                  : <textarea value={rca[field]} onChange={e => setRca({ ...rca, [field]: e.target.value })} rows={2} style={{ ...input, resize: "vertical" }} />}
              </div>
            ))}
            <button onClick={handleRCA} style={btn("#10b981")}>Submit RCA</button>
          </div>
        )}

        {incident.rca && (
          <div style={{ borderTop: "1px solid #333", paddingTop: "20px", marginTop: "8px" }}>
            <h3 style={{ color: "#10b981", marginBottom: "12px" }}>✓ RCA Submitted</h3>
            {[["Root Cause", incident.rca.root_cause], ["Timeline", incident.rca.timeline], ["Fix Applied", incident.rca.fix_applied], ["Prevention", incident.rca.prevention]].map(([k, v]) => (
              <div key={k} style={{ marginBottom: "10px" }}>
                <div style={{ color: "#666", fontSize: "11px" }}>{k}</div>
                <div style={{ color: "#ccc", fontSize: "13px" }}>{v}</div>
              </div>
            ))}
          </div>
        )}

        {msg && <div style={{ marginTop: "16px", padding: "10px 14px", background: "#13131f", borderRadius: "6px", color: "#10b981", fontSize: "13px" }}>{msg}</div>}
      </div>
    </div>
  );
}
