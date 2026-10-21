import React, { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const EMERGENCY_CATEGORIES = [
  "Immediate child protection alert",
  "Runaway / Lost child alert",
  "Medical assistance requirement",
  "Hazardous labour rescue required",
  "Other critical situation",
];

export default function EmergencyReportForm({ district = "Thiruvananthapuram", token }) {
  const [category, setCategory] = useState(EMERGENCY_CATEGORIES[0]);
  const [description, setDescription] = useState("");
  const [relatedCaseId, setRelatedCaseId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);

    try {
      const headers = { "Content-Type": "application/json" };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE_URL}/api/emergency`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          category,
          description: description.trim(),
          district,
          related_case_id: relatedCaseId.trim() || null,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Failed to log emergency event.");

      setResult(data);
      setDescription("");
      setRelatedCaseId("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 540, padding: 16, border: "2px solid #ef4444", borderRadius: 8, fontFamily: "system-ui, sans-serif" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, color: "#dc2626", marginBottom: 8 }}>
        <h3 style={{ margin: 0 }}>Log Emergency Situation Alert</h3>
      </div>

      <div style={{ padding: 10, background: "#fee2e2", borderRadius: 6, fontSize: "0.85rem", color: "#991b1b", marginBottom: 12 }}>
        <strong>PROTOTYPE SAFETY NOTICE:</strong> Recording an alert in this prototype system does <em>NOT</em> dial 112, 1098, police, or emergency medical dispatchers. In genuine life-threatening emergencies, immediately dial national emergency hotlines.
      </div>

      {error && (
        <div style={{ padding: 10, background: "#fee2e2", color: "#b91c1c", borderRadius: 4, marginBottom: 12 }}>
          {error}
        </div>
      )}

      {result ? (
        <div style={{ padding: 12, background: "#ecfdf5", border: "1px solid #10b981", borderRadius: 6 }}>
          <h4 style={{ margin: "0 0 6px 0", color: "#065f46" }}>Alert Logged Successfully</h4>
          <p style={{ margin: 0 }}>Call Reference: <strong>{result.call.call_ref}</strong> (Status: {result.call.status})</p>
          <p style={{ fontSize: "0.85rem", color: "#047857", marginTop: 4 }}>{result.disclaimer}</p>
          <button
            onClick={() => setResult(null)}
            style={{ marginTop: 8, padding: "6px 12px", background: "#dc2626", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}
          >
            Log Another Alert
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div>
            <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>Emergency Alert Category *</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
            >
              {EMERGENCY_CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>Situation Summary * (max 500 chars)</label>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              placeholder="Minimal factual summary of crisis condition..."
              style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>Related Case ID (Optional)</label>
            <input
              type="text"
              value={relatedCaseId}
              onChange={(e) => setRelatedCaseId(e.target.value)}
              placeholder="e.g. KAR-8B2A91F4"
              style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: "10px 16px",
              background: loading ? "#9ca3af" : "#dc2626",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Logging Emergency..." : "Submit Critical Alert"}
          </button>
        </form>
      )}
    </div>
  );
}
