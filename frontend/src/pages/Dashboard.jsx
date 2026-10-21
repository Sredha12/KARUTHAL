import React, { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, getOfficerSession, clearOfficerSession } from "../api";
import DistrictMap from "../components/DistrictMap";

export default function Dashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const navigate = useNavigate();
  const session = getOfficerSession();
  const isTabVisible = useRef(!document.hidden);

  useEffect(() => {
    if (!session) {
      navigate("/login");
      return;
    }

    const handleVisibilityChange = () => {
      isTabVisible.current = !document.hidden;
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);

    const loadDashboard = async () => {
      if (!isTabVisible.current) return;
      try {
        const data = await api.get(`/api/dashboard?district=${encodeURIComponent(session.district)}`);
        setDashboardData(data);
        setError("");
      } catch (err) {
        setError(err.message || "Failed to load dashboard data.");
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
    const interval = setInterval(loadDashboard, 5000);

    return () => {
      clearInterval(interval);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [navigate, session?.district]);

  const handleMarkSolved = async (numericId) => {
    setActionLoadingId(numericId);
    try {
      await api.patch(`/api/report/${numericId}`, { status: "Solved" });
      setDashboardData((prev) => {
        if (!prev) return prev;
        const updatedReports = prev.reports.map((r) =>
          r.id === numericId ? { ...r, status: "Solved" } : r
        );
        return {
          ...prev,
          solved: prev.solved + 1,
          pending: Math.max(0, prev.pending - 1),
          reports: updatedReports,
        };
      });
    } catch (err) {
      alert(`Failed to update status: ${err.message}`);
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleAcknowledgeCall = async (callId) => {
    try {
      await api.patch(`/api/emergency/${callId}`, { status: "Acknowledged" });
      setDashboardData((prev) => {
        if (!prev || !prev.calls) return prev;
        return {
          ...prev,
          calls: prev.calls.map((c) => (c.id === callId ? { ...c, status: "Acknowledged" } : c)),
        };
      });
    } catch (err) {
      alert(`Failed to acknowledge emergency call: ${err.message}`);
    }
  };

  if (!session) return null;

  return (
    <div className="officer-container">
      {/* Officer Welcome & Summary */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <h1 style={{ fontSize: "1.6rem", fontWeight: "800", color: "var(--teal-900)" }}>
            District Officer Dashboard
          </h1>
          <div style={{ display: "flex", gap: "10px", alignItems: "center", marginTop: "4px" }}>
            <span style={{ fontSize: "0.95rem", fontWeight: "600", color: "var(--text)" }}>
              {session.name}
            </span>
            <span
              style={{
                fontSize: "0.8rem",
                fontWeight: "700",
                background: "var(--teal-900)",
                color: "var(--gold)",
                padding: "2px 10px",
                borderRadius: "14px",
              }}
            >
              {session.district} District Jurisdiction
            </span>
          </div>
        </div>
      </div>

      {error && (
        <div
          style={{
            background: "var(--danger-soft)",
            border: "1px solid var(--danger)",
            color: "var(--danger)",
            borderRadius: "10px",
            padding: "12px 16px",
            marginBottom: "20px",
            fontSize: "0.9rem",
          }}
        >
          {error}
        </div>
      )}

      {/* Metrics Grid */}
      {dashboardData && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "16px",
            marginBottom: "24px",
          }}
        >
          <div className="content-card" style={{ padding: "18px", borderTop: "4px solid var(--teal-700)" }}>
            <div style={{ fontSize: "2rem", fontWeight: "800", color: "var(--teal-900)" }}>
              {dashboardData.total}
            </div>
            <div style={{ fontSize: "0.85rem", color: "var(--muted)", fontWeight: "600", textTransform: "uppercase" }}>
              Total Cases
            </div>
          </div>
          <div className="content-card" style={{ padding: "18px", borderTop: "4px solid var(--gold)" }}>
            <div style={{ fontSize: "2rem", fontWeight: "800", color: "var(--gold)" }}>
              {dashboardData.pending}
            </div>
            <div style={{ fontSize: "0.85rem", color: "var(--muted)", fontWeight: "600", textTransform: "uppercase" }}>
              Pending Review
            </div>
          </div>
          <div className="content-card" style={{ padding: "18px", borderTop: "4px solid var(--danger)" }}>
            <div style={{ fontSize: "2rem", fontWeight: "800", color: "var(--danger)" }}>
              {dashboardData.urgent}
            </div>
            <div style={{ fontSize: "0.85rem", color: "var(--muted)", fontWeight: "600", textTransform: "uppercase" }}>
              Urgent Concerns
            </div>
          </div>
          <div className="content-card" style={{ padding: "18px", borderTop: "4px solid #10b981" }}>
            <div style={{ fontSize: "2rem", fontWeight: "800", color: "#10b981" }}>
              {dashboardData.solved}
            </div>
            <div style={{ fontSize: "0.85rem", color: "var(--muted)", fontWeight: "600", textTransform: "uppercase" }}>
              Solved Cases
            </div>
          </div>
        </div>
      )}

      {/* District Map Component */}
      <DistrictMap district={session.district} />

      {/* Emergency & Helpline Calls List */}
      <div className="content-card" style={{ marginBottom: "24px", borderTop: "4px solid var(--danger)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
          <h2 style={{ fontSize: "1.2rem", fontWeight: "800", color: "var(--teal-900)" }}>
            🚨 Emergency & Helpline Events ({session.district})
          </h2>
          <span style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
            Live log from emergency helpline simulation
          </span>
        </div>

        {dashboardData?.calls && dashboardData.calls.length === 0 && (
          <div style={{ padding: "20px 0", textAlign: "center", color: "var(--muted)", fontSize: "0.9rem" }}>
            No recent emergency helpline calls logged in {session.district}.
          </div>
        )}

        {dashboardData?.calls && dashboardData.calls.length > 0 && (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid var(--line)", textAlign: "left", color: "var(--muted)" }}>
                  <th style={{ padding: "10px 12px" }}>Call Ref</th>
                  <th style={{ padding: "10px 12px" }}>Category</th>
                  <th style={{ padding: "10px 12px" }}>Description</th>
                  <th style={{ padding: "10px 12px" }}>Time</th>
                  <th style={{ padding: "10px 12px" }}>Status</th>
                  <th style={{ padding: "10px 12px" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {dashboardData.calls.map((call) => (
                  <tr key={call.id || call.call_ref} style={{ borderBottom: "1px solid var(--line)" }}>
                    <td style={{ padding: "12px", fontFamily: "var(--font-mono)", fontWeight: "700", color: "var(--teal-900)" }}>
                      {call.call_ref || call.call_id}
                    </td>
                    <td style={{ padding: "12px", fontWeight: "600" }}>{call.category}</td>
                    <td style={{ padding: "12px", color: "var(--text)" }}>{call.description}</td>
                    <td style={{ padding: "12px", color: "var(--muted)", fontSize: "0.82rem" }}>
                      {call.created_at ? new Date(call.created_at).toLocaleTimeString() : "-"}
                    </td>
                    <td style={{ padding: "12px" }}>
                      <span
                        style={{
                          fontSize: "0.78rem",
                          fontWeight: "700",
                          padding: "3px 10px",
                          borderRadius: "12px",
                          background: call.status === "Resolved" ? "#e6f4ea" : call.status === "Acknowledged" ? "var(--gold-soft)" : "var(--danger-soft)",
                          color: call.status === "Resolved" ? "#137333" : call.status === "Acknowledged" ? "#b08800" : "var(--danger)",
                        }}
                      >
                        {call.status}
                      </span>
                    </td>
                    <td style={{ padding: "12px" }}>
                      {call.status === "Active" && (
                        <button
                          type="button"
                          className="btn btn-secondary"
                          style={{ minHeight: "32px", padding: "4px 10px", fontSize: "0.8rem", width: "auto" }}
                          onClick={() => handleAcknowledgeCall(call.id)}
                        >
                          Acknowledge
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Reports Table (Panchayat removed completely) */}
      <div className="content-card" style={{ borderTop: "4px solid var(--teal-700)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px", flexWrap: "wrap", gap: "8px" }}>
          <div>
            <h2 style={{ fontSize: "1.2rem", fontWeight: "800", color: "var(--teal-900)" }}>
              District Reports & Active Inquiries
            </h2>
            <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: "2px" }}>
              Live feed of reports routed to {session.district}. Polling every 5 seconds.
            </p>
          </div>
        </div>

        {loading && <div style={{ padding: "24px 0", textAlign: "center", color: "var(--muted)" }}>Loading reports feed...</div>}

        {dashboardData?.reports && dashboardData.reports.length === 0 && (
          <div style={{ padding: "28px 0", textAlign: "center", color: "var(--muted)", fontSize: "0.92rem" }}>
            No child protection reports currently filed in {session.district}.
          </div>
        )}

        {dashboardData?.reports && dashboardData.reports.length > 0 && (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.9rem" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid var(--line)", textAlign: "left", color: "var(--muted)" }}>
                  <th style={{ padding: "12px 10px" }}>Case ID</th>
                  <th style={{ padding: "12px 10px" }}>Category</th>
                  <th style={{ padding: "12px 10px" }}>Urgency</th>
                  <th style={{ padding: "12px 10px" }}>Location Status</th>
                  <th style={{ padding: "12px 10px" }}>Status</th>
                  <th style={{ padding: "12px 10px" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {dashboardData.reports.map((report) => {
                  const caseRef = report.case_id || report.report_id || `ID-${report.id}`;
                  const isSolved = report.status === "Solved";

                  return (
                    <tr key={report.id} style={{ borderBottom: "1px solid var(--line)" }}>
                      <td style={{ padding: "12px 10px" }}>
                        <Link
                          to={`/case/${caseRef}`}
                          style={{
                            fontWeight: "700",
                            color: "var(--teal-700)",
                            fontFamily: "var(--font-mono)",
                            textDecoration: "none",
                          }}
                        >
                          {caseRef}
                        </Link>
                      </td>
                      <td style={{ padding: "12px 10px", fontWeight: "600" }}>
                        {report.category || report.abuse_type || "General"}
                      </td>
                      <td style={{ padding: "12px 10px" }}>
                        {report.is_urgent ? (
                          <span
                            style={{
                              fontSize: "0.78rem",
                              fontWeight: "700",
                              background: "var(--danger)",
                              color: "#ffffff",
                              padding: "3px 10px",
                              borderRadius: "12px",
                            }}
                          >
                            Urgent
                          </span>
                        ) : (
                          <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Standard</span>
                        )}
                      </td>
                      <td style={{ padding: "12px 10px" }}>
                        {report.has_location ? (
                          <span
                            style={{
                              fontSize: "0.78rem",
                              fontWeight: "700",
                              background: "rgba(201, 162, 39, 0.15)",
                              color: "#735c00",
                              border: "1px solid var(--gold)",
                              padding: "2px 8px",
                              borderRadius: "10px",
                            }}
                          >
                            Consented (~1km)
                          </span>
                        ) : (
                          <span style={{ color: "var(--muted)" }}>-</span>
                        )}
                      </td>
                      <td style={{ padding: "12px 10px" }}>
                        <span
                          style={{
                            fontSize: "0.78rem",
                            fontWeight: "700",
                            padding: "3px 10px",
                            borderRadius: "12px",
                            background: isSolved ? "#e6f4ea" : "#eef3f1",
                            color: isSolved ? "#137333" : "var(--teal-900)",
                          }}
                        >
                          {report.status}
                        </span>
                      </td>
                      <td style={{ padding: "12px 10px" }}>
                        <div style={{ display: "flex", gap: "8px" }}>
                          <Link
                            to={`/case/${caseRef}`}
                            className="btn btn-secondary"
                            style={{ minHeight: "34px", padding: "4px 12px", fontSize: "0.82rem", width: "auto" }}
                          >
                            Open
                          </Link>
                          {!isSolved && (
                            <button
                              type="button"
                              className="btn btn-primary"
                              style={{
                                minHeight: "34px",
                                padding: "4px 12px",
                                fontSize: "0.82rem",
                                width: "auto",
                                background: "#10b981",
                              }}
                              onClick={() => handleMarkSolved(report.id)}
                              disabled={actionLoadingId === report.id}
                            >
                              {actionLoadingId === report.id ? "Saving..." : "Mark Solved"}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
