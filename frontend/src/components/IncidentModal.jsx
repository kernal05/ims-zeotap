import { useState } from "react";
import { updateStatus, submitRCA } from "../api";

const ROOT_CAUSE_CATEGORIES = [
  "Infrastructure Failure","Database Overload","Network Partition",
  "Memory Leak","Configuration Error","Dependency Failure",
  "Capacity Exhaustion","Software Bug","Security Incident",
  "Human Error","Third-party Service Outage","Unknown",
];

export default function IncidentModal({ incident, onClose, onRefresh }) {
  const [assignee, setAssignee] = useState(incident.assigned_to || "");
  const [rca, setRca] = useState({ root_cause: "", root_cause_category: "", incident_start: "", incident_end: "", timeline: "", fix_applied: "", prevention: "", written_by: "" });
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState("success");

  const handleTransition = async (newStatus) => {
    try { await updateStatus(incident.id, { status: newStatus, assigned_to: assignee || undefined }); setMsg(`Status updated to ${newStatus}`); setMsgType("success"); onRefresh(); }
    catch (e) { setMsg(e.response?.data?.detail || "Error updating status"); setMsgType("error"); }
  };
  const handleAssign = async () => {
    try { await updateStatus(incident.id, { assigned_to: assignee }); setMsg("Assigned successfully"); setMsgType("success"); onRefresh(); }
    catch (e) { setMsg("Error assigning"); setMsgType("error"); }
  };
  const handleRCA = async () => {
    const timelineText = rca.timeline || (rca.incident_start && rca.incident_end ? `Incident started at ${rca.incident_start}, resolved at ${rca.incident_end}` : rca.timeline);
    const payload = { root_cause: rca.root_cause_category ? `[${rca.root_cause_category}] ${rca.root_cause}` : rca.root_cause, timeline: timelineText, fix_applied: rca.fix_applied, prevention: rca.prevention, written_by: rca.written_by };
    try { await submitRCA(incident.id, payload); setMsg("RCA submitted successfully!"); setMsgType("success"); onRefresh(); }
    catch (e) { setMsg(e.response?.data?.detail || "Error submitting RCA"); setMsgType("error"); }
  };

  const overlay = { position:"fixed",top:0,left:0,right:0,bottom:0,background:"rgba(0,0,0,0.7)",display:"flex",alignItems:"center",justifyContent:"center",zIndex:1000 };
  const modal = { background:"#1e1e2e",borderRadius:"12px",padding:"32px",width:"640px",maxHeight:"88vh",overflowY:"auto",position:"relative" };
  const input = { width:"100%",background:"#13131f",border:"1px solid #333",borderRadius:"6px",padding:"8px 12px",color:"#fff",fontSize:"14px",marginBottom:"10px",boxSizing:"border-box" };
  const lbl = { color:"#888",fontSize:"12px",display:"block",marginBottom:"4px" };
  const btn = (color) => ({ background:color,color:"#fff",border:"none",borderRadius:"6px",padding:"8px 18px",cursor:"pointer",fontSize:"13px",fontWeight:600,marginRight:"8px" });

  let mttrDisplay = null;
  if (rca.incident_start && rca.incident_end) {
    const diffMin = Math.round((new Date(rca.incident_end) - new Date(rca.incident_start)) / 60000);
    if (diffMin > 0) mttrDisplay = diffMin >= 60 ? `${Math.floor(diffMin/60)}h ${diffMin%60}m` : `${diffMin} min`;
  }

  return (
    <div style={overlay} onClick={onClose}>
      <div style={modal} onClick={e => e.stopPropagation()}>
        <button onClick={onClose} style={{ position:"absolute",top:16,right:16,background:"none",border:"none",color:"#888",fontSize:"20px",cursor:"pointer" }}>✕</button>
        <h2 style={{ color:"#fff",marginBottom:"4px" }}>{incident.title}</h2>
        <p style={{ color:"#888",fontSize:"13px",marginBottom:"16px" }}>ID: {incident.id}</p>
        <p style={{ color:"#ccc",marginBottom:"16px" }}>{incident.description}</p>

        <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr",gap:"12px",marginBottom:"20px" }}>
          {[["Severity",incident.severity],["Status",incident.status],["Service",incident.service_affected],["Source",incident.alert_source]].map(([k,v]) => (
            <div key={k} style={{ background:"#13131f",borderRadius:"6px",padding:"10px 14px" }}>
              <div style={{ color:"#666",fontSize:"11px" }}>{k}</div>
              <div style={{ color:"#fff",fontWeight:600 }}>{v}</div>
            </div>
          ))}
        </div>

        <div style={{ marginBottom:"20px" }}>
          <label style={lbl}>Assign To</label>
          <div style={{ display:"flex",gap:"8px",marginTop:"4px" }}>
            <input value={assignee} onChange={e => setAssignee(e.target.value)} placeholder="Engineer name" style={{ ...input,marginBottom:0,flex:1 }} />
            <button onClick={handleAssign} style={btn("#6366f1")}>Assign</button>
          </div>
        </div>

        {incident.allowed_transitions?.length > 0 && (
          <div style={{ marginBottom:"20px" }}>
            <label style={lbl}>Move Status To</label>
            <div style={{ marginTop:"6px" }}>
              {incident.allowed_transitions.map(t => (
                <button key={t} onClick={() => handleTransition(t)} style={btn(t==="closed"?"#6b7280":t==="resolved"?"#10b981":"#f59e0b")}>{t.toUpperCase()}</button>
              ))}
            </div>
          </div>
        )}

        {!incident.rca && (
          <div style={{ borderTop:"1px solid #333",paddingTop:"20px",marginTop:"8px" }}>
            <h3 style={{ color:"#fff",marginBottom:"16px" }}>Submit RCA Report</h3>

            <div style={{ marginBottom:"10px" }}>
              <label style={lbl}>Root Cause Category *</label>
              <select value={rca.root_cause_category} onChange={e => setRca({...rca,root_cause_category:e.target.value})} style={{ ...input,appearance:"none",cursor:"pointer" }}>
                <option value="">— Select a category —</option>
                {ROOT_CAUSE_CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div style={{ marginBottom:"10px" }}>
              <label style={lbl}>Root Cause Description *</label>
              <textarea value={rca.root_cause} onChange={e => setRca({...rca,root_cause:e.target.value})} rows={2} placeholder="Describe the root cause..." style={{ ...input,resize:"vertical" }} />
            </div>

            <div style={{ display:"grid",gridTemplateColumns:"1fr 1fr",gap:"12px",marginBottom:"10px" }}>
              <div>
                <label style={lbl}>Incident Start *</label>
                <input type="datetime-local" value={rca.incident_start} onChange={e => setRca({...rca,incident_start:e.target.value})} style={{ ...input,marginBottom:0,colorScheme:"dark" }} />
              </div>
              <div>
                <label style={lbl}>Incident End *</label>
                <input type="datetime-local" value={rca.incident_end} onChange={e => setRca({...rca,incident_end:e.target.value})} style={{ ...input,marginBottom:0,colorScheme:"dark" }} />
              </div>
            </div>

            {mttrDisplay && (
              <div style={{ marginBottom:"10px",padding:"8px 12px",background:"#0d2137",borderRadius:"6px",border:"1px solid #1d4ed8" }}>
                <span style={{ color:"#60a5fa",fontSize:"13px" }}>Calculated MTTR: <strong>{mttrDisplay}</strong></span>
              </div>
            )}

            <div style={{ marginBottom:"10px" }}>
              <label style={lbl}>Timeline *</label>
              <textarea value={rca.timeline} onChange={e => setRca({...rca,timeline:e.target.value})} rows={2} placeholder="Sequence of events..." style={{ ...input,resize:"vertical" }} />
            </div>
            <div style={{ marginBottom:"10px" }}>
              <label style={lbl}>Fix Applied *</label>
              <textarea value={rca.fix_applied} onChange={e => setRca({...rca,fix_applied:e.target.value})} rows={2} placeholder="What was done to resolve?" style={{ ...input,resize:"vertical" }} />
            </div>
            <div style={{ marginBottom:"10px" }}>
              <label style={lbl}>Prevention Steps *</label>
              <textarea value={rca.prevention} onChange={e => setRca({...rca,prevention:e.target.value})} rows={2} placeholder="How to prevent in future?" style={{ ...input,resize:"vertical" }} />
            </div>
            <div style={{ marginBottom:"16px" }}>
              <label style={lbl}>Written By *</label>
              <input value={rca.written_by} onChange={e => setRca({...rca,written_by:e.target.value})} placeholder="Your name" style={input} />
            </div>
            <button onClick={handleRCA} style={btn("#10b981")}>Submit RCA</button>
          </div>
        )}

        {incident.rca && (
          <div style={{ borderTop:"1px solid #333",paddingTop:"20px",marginTop:"8px" }}>
            <h3 style={{ color:"#10b981",marginBottom:"12px" }}>✓ RCA Submitted</h3>
            {[["Root Cause",incident.rca.root_cause],["Timeline",incident.rca.timeline],["Fix Applied",incident.rca.fix_applied],["Prevention",incident.rca.prevention],["Written By",incident.rca.written_by]].map(([k,v]) => (
              <div key={k} style={{ marginBottom:"10px" }}>
                <div style={{ color:"#666",fontSize:"11px" }}>{k}</div>
                <div style={{ color:"#ccc",fontSize:"13px" }}>{v}</div>
              </div>
            ))}
          </div>
        )}

        {msg && <div style={{ marginTop:"16px",padding:"10px 14px",background:"#13131f",borderRadius:"6px",fontSize:"13px",color:msgType==="error"?"#f87171":"#10b981" }}>{msg}</div>}
      </div>
    </div>
  );
}
