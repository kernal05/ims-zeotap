const SEVERITY_COLORS = { P1: "#ef4444", P2: "#f59e0b", P3: "#6366f1" };
const STATUS_COLORS = {
  open: "#f59e0b", investigating: "#6366f1",
  mitigating: "#f97316", resolved: "#10b981", closed: "#6b7280"
};

export default function IncidentTable({ incidents, onSelect }) {
  if (!incidents?.length) return <p style={{ color: "#888", textAlign: "center", padding: "40px" }}>No incidents found.</p>;
  return (
    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
      <thead>
        <tr style={{ borderBottom: "1px solid #333" }}>
          {["Title", "Severity", "Status", "Service", "Assigned To", "Created"].map(h => (
            <th key={h} style={{ padding: "12px 16px", textAlign: "left", color: "#888", fontWeight: 600 }}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {incidents.map(inc => (
          <tr key={inc.id} onClick={() => onSelect(inc)}
            style={{ borderBottom: "1px solid #222", cursor: "pointer", transition: "background 0.15s" }}
            onMouseEnter={e => e.currentTarget.style.background = "#1e1e2e"}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
            <td style={{ padding: "12px 16px", color: "#fff", maxWidth: "200px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{inc.title}</td>
            <td style={{ padding: "12px 16px" }}>
              <span style={{ background: SEVERITY_COLORS[inc.severity], color: "#fff", padding: "2px 10px", borderRadius: "12px", fontSize: "12px", fontWeight: 700 }}>{inc.severity}</span>
            </td>
            <td style={{ padding: "12px 16px" }}>
              <span style={{ background: STATUS_COLORS[inc.status], color: "#fff", padding: "2px 10px", borderRadius: "12px", fontSize: "12px" }}>{inc.status}</span>
            </td>
            <td style={{ padding: "12px 16px", color: "#ccc" }}>{inc.service_affected}</td>
            <td style={{ padding: "12px 16px", color: "#ccc" }}>{inc.assigned_to || "—"}</td>
            <td style={{ padding: "12px 16px", color: "#888" }}>{new Date(inc.created_at).toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
