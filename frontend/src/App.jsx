import { useState, useEffect, useCallback } from "react";
import { getIncidents, getStats } from "./api";
import StatsBar from "./components/StatsBar";
import IncidentTable from "./components/IncidentTable";
import IncidentModal from "./components/IncidentModal";
import CreateIncident from "./components/CreateIncident";

export default function App() {
  const [incidents, setIncidents] = useState([]);
  const [stats, setStats] = useState(null);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  const fetchAll = useCallback(async () => {
    try {
      const [inc, st] = await Promise.all([getIncidents(), getStats()]);
      setIncidents(inc);
      setStats(st);
    } catch (e) {
      console.error("API error", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchAll(); const t = setInterval(fetchAll, 30000); return () => clearInterval(t); }, [fetchAll]);

  const handleSelect = (inc) => setSelected(inc);
  const handleClose = () => { setSelected(null); fetchAll(); };

  const filtered = filter === "all" ? incidents : incidents.filter(i =>
    filter === "open" ? ["open", "investigating", "mitigating"].includes(i.status) :
    filter === "p1" ? i.severity === "P1" :
    i.status === filter
  );

  return (
    <div style={{ minHeight: "100vh", background: "#0d0d1a", color: "#fff", fontFamily: "'Inter', sans-serif", padding: "32px" }}>
      <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "28px" }}>
          <div>
            <h1 style={{ fontSize: "24px", fontWeight: 800, color: "#fff", margin: 0 }}>🚨 Incident Management System</h1>
            <p style={{ color: "#666", fontSize: "13px", margin: "4px 0 0" }}>Mission-Critical Operations Dashboard</p>
          </div>
          <CreateIncident onRefresh={fetchAll} />
        </div>

        <StatsBar stats={stats} />

        <div style={{ background: "#1e1e2e", borderRadius: "10px", padding: "24px" }}>
          <div style={{ display: "flex", gap: "8px", marginBottom: "20px" }}>
            {["all", "open", "p1", "resolved", "closed"].map(f => (
              <button key={f} onClick={() => setFilter(f)}
                style={{ background: filter === f ? "#6366f1" : "#13131f", color: filter === f ? "#fff" : "#888", border: "none", borderRadius: "6px", padding: "6px 16px", cursor: "pointer", fontSize: "13px", fontWeight: 600, textTransform: "capitalize" }}>
                {f === "p1" ? "P1 Only" : f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            ))}
          </div>

          {loading ? (
            <p style={{ color: "#666", textAlign: "center", padding: "40px" }}>Loading incidents...</p>
          ) : (
            <IncidentTable incidents={filtered} onSelect={handleSelect} />
          )}
        </div>

        <p style={{ color: "#333", fontSize: "12px", textAlign: "center", marginTop: "20px" }}>
          Auto-refreshes every 30s · IMS v1.0.0
        </p>
      </div>

      {selected && <IncidentModal incident={selected} onClose={handleClose} onRefresh={fetchAll} />}
    </div>
  );
}
