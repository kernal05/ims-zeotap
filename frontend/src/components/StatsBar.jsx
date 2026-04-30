export default function StatsBar({ stats }) {
  if (!stats) return null;
  const cards = [
    { label: "Total Incidents", value: stats.total, color: "#6366f1" },
    { label: "Open", value: stats.open, color: "#f59e0b" },
    { label: "P1 Active", value: stats.p1_active, color: "#ef4444" },
    { label: "Avg MTTR (min)", value: stats.avg_mttr_minutes, color: "#10b981" },
  ];
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: "16px", marginBottom: "24px" }}>
      {cards.map(c => (
        <div key={c.label} style={{ background: "#1e1e2e", borderRadius: "8px", padding: "20px", borderLeft: `4px solid ${c.color}` }}>
          <div style={{ color: "#888", fontSize: "13px" }}>{c.label}</div>
          <div style={{ color: "#fff", fontSize: "32px", fontWeight: "700", marginTop: "8px" }}>{c.value}</div>
        </div>
      ))}
    </div>
  );
}
