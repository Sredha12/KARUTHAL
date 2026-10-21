import React, { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const VISIT_OUTCOMES = [
  "Safe with family",
  "Needs support services",
  "Further assessment required",
  "Child relocated to safe care",
  "No concern detected",
];

export default function FieldVisitForm({ caseId, token, onVisitRecorded }) {
  const [outcome, setOutcome] = useState(VISIT_OUTCOMES[0]);
  const [notes, setNotes] = useState("");
  const [visitAt, setVisitAt] = useState(new Date().toISOString().slice(0, 16));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/cases/${caseId}/field-visits`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          visit_at: new Date(visitAt).toISOString(),
          outcome,
          notes: notes.trim(),
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.message || "Failed to log field visit.");
      }

      setSuccess("Field visit recorded successfully. Case status updated to 'Visit Recorded'.");
      setNotes("");
      if (onVisitRecorded) onVisitRecorded(data.field_visit);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 540, padding: 16, border: "1px solid #e5e7eb", borderRadius: 8, fontFamily: "system-ui, sans-serif" }}>
      <h3 style={{ marginTop: 0 }}>Log On-Site Field Visit: Case {caseId}</h3>
      <p style={{ fontSize: "0.85rem", color: "#6b7280" }}>
        Privacy Guarantee: No GPS coordinates or geographical telemetry are captured by this form.
      </p>

      {error && (
        <div style={{ padding: 10, background: "#fee2e2", color: "#b91c1c", borderRadius: 4, marginBottom: 12 }}>
          {error}
        </div>
      )}
      {success && (
        <div style={{ padding: 10, background: "#ecfdf5", color: "#065f46", borderRadius: 4, marginBottom: 12 }}>
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <div>
          <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>Date & Time of Assessment Visit *</label>
          <input
            type="datetime-local"
            value={visitAt}
            onChange={(e) => setVisitAt(e.target.value)}
            required
            style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
          />
        </div>

        <div>
          <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>Visit Assessment Outcome *</label>
          <select
            value={outcome}
            onChange={(e) => setOutcome(e.target.value)}
            style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
          >
            {VISIT_OUTCOMES.map((out) => (
              <option key={out} value={out}>
                {out}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>
            Caseworker Assessment Observations * (max 2000 chars)
          </label>
          <textarea
            rows={4}
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            required
            placeholder="Document living conditions, family response, and support recommendations without child names..."
            style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            padding: "10px 16px",
            background: loading ? "#9ca3af" : "#059669",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Recording Visit..." : "Submit Field Assessment"}
        </button>
      </form>
    </div>
  );
}
