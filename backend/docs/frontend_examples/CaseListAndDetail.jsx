import React, { useState, useEffect } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function CaseListAndDetail({ token, officerDistrict }) {
  const [cases, setCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const fetchCases = async () => {
    setLoading(true);
    setError("");
    try {
      let url = `${API_BASE_URL}/api/cases?limit=50`;
      if (statusFilter) url += `&status=${encodeURIComponent(statusFilter)}`;

      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Failed to load cases");

      setCases(data.cases || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) fetchCases();
  }, [token, statusFilter]);

  const viewCaseDetail = async (caseId) => {
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/cases/${caseId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Failed to load case detail");
      setSelectedCase(data);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", padding: 16 }}>
      <h2>Case File Management: {officerDistrict} Jurisdiction</h2>

      {error && (
        <div style={{ padding: 10, background: "#fee2e2", color: "#b91c1c", borderRadius: 4, marginBottom: 12 }}>
          {error}
        </div>
      )}

      <div style={{ marginBottom: 16, display: "flex", gap: 12, alignItems: "center" }}>
        <label>Filter by Status:</label>
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All Statuses</option>
          <option value="Submitted">Submitted</option>
          <option value="Under Review">Under Review</option>
          <option value="Assigned">Assigned</option>
          <option value="Visit Recorded">Visit Recorded</option>
          <option value="Referred">Referred</option>
          <option value="Solved">Solved</option>
        </select>
        <button onClick={fetchCases} disabled={loading} style={{ padding: "4px 10px" }}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: 16 }}>
        {/* Left: Case List Table */}
        <div style={{ border: "1px solid #e5e7eb", borderRadius: 6, overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
            <thead style={{ background: "#f3f4f6", borderBottom: "1px solid #e5e7eb" }}>
              <tr>
                <th style={{ padding: 8, textAlign: "left" }}>Case ID</th>
                <th style={{ padding: 8, textAlign: "left" }}>Category</th>
                <th style={{ padding: 8, textAlign: "left" }}>Panchayat</th>
                <th style={{ padding: 8, textAlign: "left" }}>Status</th>
                <th style={{ padding: 8 }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {cases.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ padding: 16, textAlign: "center", color: "#6b7280" }}>
                    No cases match the selected filter.
                  </td>
                </tr>
              ) : (
                cases.map((c) => (
                  <tr key={c.id} style={{ borderBottom: "1px solid #f3f4f6" }}>
                    <td style={{ padding: 8, fontWeight: 600 }}>{c.case_id}</td>
                    <td style={{ padding: 8 }}>{c.category}</td>
                    <td style={{ padding: 8 }}>{c.panchayat}</td>
                    <td style={{ padding: 8 }}>
                      <span
                        style={{
                          padding: "2px 6px",
                          borderRadius: 4,
                          fontSize: "0.8rem",
                          background: c.status === "Solved" ? "#d1fae5" : c.is_urgent ? "#fee2e2" : "#e0e7ff",
                          color: c.status === "Solved" ? "#065f46" : c.is_urgent ? "#991b1b" : "#3730a3",
                        }}
                      >
                        {c.status}
                      </span>
                    </td>
                    <td style={{ padding: 8, textAlign: "center" }}>
                      <button onClick={() => viewCaseDetail(c.case_id)} style={{ padding: "4px 8px", cursor: "pointer" }}>
                        View
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Right: Selected Case Details */}
        <div style={{ border: "1px solid #e5e7eb", borderRadius: 6, padding: 16, background: "#fafafa" }}>
          {selectedCase ? (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <h3 style={{ margin: "0 0 8px 0" }}>Case File: {selectedCase.case_id}</h3>
                <span style={{ fontWeight: 600, color: "#4f46e5" }}>Status: {selectedCase.status}</span>
              </div>
              <p>
                <strong>District:</strong> {selectedCase.district} | <strong>Panchayat:</strong> {selectedCase.panchayat}
              </p>
              <p>
                <strong>Concern Category:</strong> {selectedCase.category}
              </p>
              <p>
                <strong>Urgency:</strong> {selectedCase.is_urgent ? "URGENT ATTENTION" : "Standard"}
              </p>
              <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 4, padding: 12, marginTop: 12 }}>
                <strong>Intake Observations:</strong>
                <p style={{ marginTop: 6, color: "#374151" }}>{selectedCase.description}</p>
              </div>
              <p style={{ fontSize: "0.8rem", color: "#6b7280", marginTop: 12 }}>
                Registered At: {selectedCase.created_at} | Last Updated: {selectedCase.updated_at}
              </p>
            </div>
          ) : (
            <div style={{ textAlign: "center", color: "#9ca3af", marginTop: 40 }}>
              Select a case from the table to view confidential file details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
