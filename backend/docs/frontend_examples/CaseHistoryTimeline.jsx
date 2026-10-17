import React, { useState, useEffect } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function CaseHistoryTimeline({ caseId, token }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchHistory = async () => {
    if (!caseId) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/cases/${caseId}/history`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Failed to load audit trail.");
      setHistory(data.history || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [caseId, token]);

  return (
    <div style={{ maxWidth: 580, padding: 16, fontFamily: "system-ui, sans-serif" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Chain of Custody & Audit Trail: {caseId}</h3>
        <button onClick={fetchHistory} disabled={loading} style={{ padding: "4px 8px", cursor: "pointer" }}>
          {loading ? "..." : "Refresh"}
        </button>
      </div>

      <p style={{ fontSize: "0.85rem", color: "#6b7280", margin: "0 0 16px 0" }}>
        Immutable record of operational actions. No personal descriptions or private notes are exposed.
      </p>

      {error && (
        <div style={{ padding: 10, background: "#fee2e2", color: "#b91c1c", borderRadius: 4, marginBottom: 12 }}>
          {error}
        </div>
      )}

      {history.length === 0 ? (
        <div style={{ color: "#9ca3af", textAlign: "center", padding: 20 }}>No audit events logged yet.</div>
      ) : (
        <div style={{ borderLeft: "2px solid #e5e7eb", marginLeft: 8, paddingLeft: 16, display: "flex", flexDirection: "column", gap: 14 }}>
          {history.map((event) => (
            <div key={event.id} style={{ position: "relative" }}>
              {/* Timeline marker */}
              <div
                style={{
                  position: "absolute",
                  left: -22,
                  top: 4,
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  background: "#4f46e5",
                }}
              />
              <div style={{ fontSize: "0.95rem", fontWeight: 600, color: "#1f2937" }}>{event.action}</div>
              {event.details && (
                <div style={{ fontSize: "0.85rem", color: "#4b5563", marginTop: 2 }}>{event.details}</div>
              )}
              <div style={{ fontSize: "0.75rem", color: "#9ca3af", marginTop: 4 }}>
                {event.created_at ? new Date(event.created_at).toLocaleString() : ""}
                {event.actor_name ? ` • by ${event.actor_name}` : " • System logged"}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
