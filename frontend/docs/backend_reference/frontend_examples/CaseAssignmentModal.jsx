import React, { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function CaseAssignmentModal({ caseId, token, availableFieldOfficers, onClose, onAssigned }) {
  const [selectedOfficerId, setSelectedOfficerId] = useState(
    availableFieldOfficers?.[0]?.id || ""
  );
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAssign = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/cases/${caseId}/assign`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          field_officer_id: parseInt(selectedOfficerId, 10),
          notes: notes.trim(),
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.message || "Failed to assign case.");
      }

      onAssigned(data.assignment);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        background: "rgba(0,0,0,0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <div style={{ background: "#fff", padding: 24, borderRadius: 8, width: 440, maxWidth: "90%" }}>
        <h3 style={{ marginTop: 0 }}>Assign Field Officer to Case: {caseId}</h3>

        {error && (
          <div style={{ padding: 10, background: "#fee2e2", color: "#b91c1c", borderRadius: 4, marginBottom: 12 }}>
            {error}
          </div>
        )}

        <form onSubmit={handleAssign} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div>
            <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>
              Select Active Field Officer *
            </label>
            <select
              value={selectedOfficerId}
              onChange={(e) => setSelectedOfficerId(e.target.value)}
              required
              style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
            >
              {availableFieldOfficers.map((fo) => (
                <option key={fo.id} value={fo.id}>
                  {fo.name} ({fo.officer_code}) - {fo.district}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>
              Assignment Directives / Instructions
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Conduct assessment of living conditions during school hours..."
              style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 8 }}>
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              style={{ padding: "8px 14px", border: "1px solid #ccc", background: "#f3f4f6", borderRadius: 4, cursor: "pointer" }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              style={{
                padding: "8px 16px",
                background: loading ? "#9ca3af" : "#2563eb",
                color: "#fff",
                border: "none",
                borderRadius: 4,
                cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "Assigning..." : "Confirm Assignment"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
