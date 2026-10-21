import React, { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function AiSummaryPanel({ caseId, token }) {
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const generateSummary = async () => {
    if (!caseId) return;
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_BASE_URL}/api/cases/${caseId}/ai-summary`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Failed to generate AI summary.");
      setSummaryData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 640, padding: 18, border: "1px solid #c7d2fe", background: "#f8faff", borderRadius: 8, fontFamily: "system-ui, sans-serif" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h3 style={{ margin: 0, color: "#1e1b4b" }}>AI Decision-Support Summary</h3>
        <button
          onClick={generateSummary}
          disabled={loading}
          style={{
            padding: "8px 14px",
            background: loading ? "#9ca3af" : "#4f46e5",
            color: "#fff",
            border: "none",
            borderRadius: 6,
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Generating..." : summaryData ? "Regenerate Summary" : "Generate Case Summary"}
        </button>
      </div>

      {error && (
        <div style={{ padding: 10, background: "#fee2e2", color: "#b91c1c", borderRadius: 4, marginBottom: 12 }}>
          {error}
        </div>
      )}

      {summaryData ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {/* Mandatory Safety Badges and Disclaimer */}
          <div style={{ padding: 10, background: "#fef3c7", border: "1px solid #f59e0b", borderRadius: 6 }}>
            <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
              <span style={{ background: "#d97706", color: "#fff", padding: "2px 6px", borderRadius: 4, fontSize: "0.75rem", fontWeight: 700 }}>
                UNVERIFIED INTAKE
              </span>
              <span style={{ background: "#b45309", color: "#fff", padding: "2px 6px", borderRadius: 4, fontSize: "0.75rem", fontWeight: 700 }}>
                HUMAN REVIEW REQUIRED
              </span>
            </div>
            <div style={{ fontSize: "0.85rem", color: "#92400e" }}>{summaryData.disclaimer}</div>
          </div>

          {/* Structured Summary */}
          <div style={{ background: "#fff", padding: 12, borderRadius: 6, border: "1px solid #e0e7ff" }}>
            <h4 style={{ margin: "0 0 6px 0", color: "#3730a3" }}>Structured Synthesis</h4>
            <p style={{ margin: 0, fontSize: "0.9rem", color: "#1f2937", lineHeight: 1.5 }}>
              {summaryData.structured_summary}
            </p>
          </div>

          {/* Missing Information Checklist */}
          <div style={{ background: "#fff", padding: 12, borderRadius: 6, border: "1px solid #e0e7ff" }}>
            <h4 style={{ margin: "0 0 8px 0", color: "#3730a3" }}>Missing Information Checklist</h4>
            <ul style={{ margin: 0, paddingLeft: 20, fontSize: "0.85rem", color: "#374151" }}>
              {summaryData.missing_information.map((item, idx) => (
                <li key={idx} style={{ marginBottom: 4 }}>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* Related Historical Hints (Aggregate only) */}
          <div style={{ background: "#fff", padding: 12, borderRadius: 6, border: "1px solid #e0e7ff" }}>
            <h4 style={{ margin: "0 0 8px 0", color: "#3730a3" }}>District Historical Context</h4>
            {summaryData.related_case_hints.map((hint, idx) => (
              <div key={idx} style={{ fontSize: "0.85rem", color: "#4b5563" }}>
                Similar concerns ({hint.category}) in {hint.district}: <strong>{hint.similar_cases_count} past records</strong>
                <div style={{ fontSize: "0.75rem", color: "#6b7280", marginTop: 2 }}>{hint.note}</div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div style={{ textAlign: "center", color: "#6b7280", padding: "24px 0", fontSize: "0.9rem" }}>
          Click "Generate Case Summary" to request a deterministic, privacy-safe decision support synthesis.
        </div>
      )}
    </div>
  );
}
