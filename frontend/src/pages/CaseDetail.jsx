import React, { useState, useEffect, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { api, getOfficerSession } from "../api";

export default function CaseDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const session = getOfficerSession();

  const [caseData, setCaseData] = useState(null);
  const [locationData, setLocationData] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [callsData, setCallsData] = useState([]);
  const [activeCall, setActiveCall] = useState(null);
  const [callDuration, setCallDuration] = useState(0);

  // AI summary state
  const [aiSummary, setAiSummary] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [callActionLoading, setCallActionLoading] = useState(false);
  const [callNotice, setCallNotice] = useState("");
  const [overrideSolved, setOverrideSolved] = useState(false);

  const wsRef = useRef(null);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!session) {
      navigate("/login");
      return;
    }

    const loadAllCaseDetails = async () => {
      setLoading(true);
      setError("");

      try {
        // 1. Core case info
        const cData = await api.get(`/api/cases/${id}`);
        setCaseData(cData);

        // 2. Consented location
        try {
          const lData = await api.get(`/api/cases/${id}/location`);
          setLocationData(lData);
        } catch (lErr) {
          console.warn("Location error:", lErr.message);
        }

        // 3. Case history
        try {
          const hData = await api.get(`/api/cases/${id}/history`);
          setHistoryData(hData.history || []);
        } catch (hErr) {
          console.warn("History error:", hErr.message);
        }

        // 4. Case calls
        try {
          const clData = await api.get(`/api/cases/${id}/calls`);
          setCallsData(clData.calls || []);
          const ongoing = clData.calls.find((c) =>
            ["requested", "ringing", "connected"].includes(c.status)
          );
          setActiveCall(ongoing || null);
          if (ongoing?.notice) setCallNotice(ongoing.notice);
        } catch (cErr) {
          console.warn("Calls error:", cErr.message);
        }
      } catch (err) {
        setError(err.message || "Failed to load case data.");
      } finally {
        setLoading(false);
      }
    };

    loadAllCaseDetails();

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [id, navigate, session?.district]);

  // Duration timer for active call
  useEffect(() => {
    if (activeCall?.status === "connected") {
      timerRef.current = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
      setCallDuration(0);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [activeCall?.status]);

  // WebSocket signaling for simulated call
  const connectCallWebSocket = (sessionId) => {
    if (wsRef.current) wsRef.current.close();

    const wsUrl = `ws://${window.location.hostname}:8000/api/calls/ws/${sessionId}`;
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.status) {
            setActiveCall((prev) => (prev ? { ...prev, status: data.status } : null));
          }
          if (data.notice) {
            setCallNotice(data.notice);
          }
        } catch {}
      };

      ws.onclose = () => {
        // Disconnected
      };
    } catch (e) {
      console.warn("WebSocket setup note:", e.message);
    }
  };

  const handleStartCall = async () => {
    setCallActionLoading(true);
    setCallNotice("");
    try {
      const res = await api.post(`/api/cases/${id}/call`, {
        override_solved: overrideSolved,
      });
      setActiveCall(res.call);
      setCallNotice(res.call.notice || "Simulated call initiated.");
      connectCallWebSocket(res.call.session_id || res.call.id);
      refreshCalls();
    } catch (err) {
      alert(`Could not start call: ${err.message}`);
    } finally {
      setCallActionLoading(false);
    }
  };

  const handleAcceptCall = async (callId) => {
    setCallActionLoading(true);
    try {
      const res = await api.post(`/api/calls/${callId}/accept`);
      setActiveCall(res.call);
      if (res.call.notice) setCallNotice(res.call.notice);
      refreshCalls();
    } catch (err) {
      alert(`Failed to accept call: ${err.message}`);
    } finally {
      setCallActionLoading(false);
    }
  };

  const handleEndCall = async (callId) => {
    setCallActionLoading(true);
    try {
      await api.post(`/api/calls/${callId}/end`);
      if (wsRef.current) wsRef.current.close();
      setActiveCall(null);
      refreshCalls();
    } catch (err) {
      alert(`Failed to end call: ${err.message}`);
    } finally {
      setCallActionLoading(false);
    }
  };

  const refreshCalls = async () => {
    try {
      const clData = await api.get(`/api/cases/${id}/calls`);
      setCallsData(clData.calls || []);
      const ongoing = clData.calls.find((c) =>
        ["requested", "ringing", "connected"].includes(c.status)
      );
      setActiveCall(ongoing || null);
    } catch {}
  };

  const handleRequestAiSummary = async () => {
    setAiLoading(true);
    try {
      const res = await api.post(`/api/cases/${id}/ai-summary`);
      setAiSummary(res);
    } catch (err) {
      alert(`AI Summary request failed: ${err.message}`);
    } finally {
      setAiLoading(false);
    }
  };

  const formatTimer = (sec) => {
    const m = Math.floor(sec / 60).toString().padStart(2, "0");
    const s = (sec % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  if (!session) return null;

  return (
    <div className="officer-container">
      <div style={{ marginBottom: "16px" }}>
        <Link
          to="/dashboard"
          style={{
            fontSize: "0.9rem",
            fontWeight: "700",
            color: "var(--teal-700)",
            textDecoration: "none",
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
          }}
        >
          ← Back to Dashboard
        </Link>
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
          }}
        >
          {error}
        </div>
      )}

      {/* Case Overview Card */}
      {caseData && (
        <div className="content-card" style={{ borderTop: "4px solid var(--teal-700)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "10px" }}>
            <div>
              <h1 style={{ fontSize: "1.4rem", fontWeight: "800", color: "var(--teal-900)" }}>
                Case File: {caseData.case_id || caseData.report_id}
              </h1>
              <div style={{ display: "flex", gap: "8px", marginTop: "6px", alignItems: "center" }}>
                <span
                  style={{
                    fontSize: "0.8rem",
                    fontWeight: "700",
                    padding: "3px 10px",
                    borderRadius: "12px",
                    background: caseData.status === "Solved" ? "#e6f4ea" : "#eef3f1",
                    color: caseData.status === "Solved" ? "#137333" : "var(--teal-900)",
                  }}
                >
                  Status: {caseData.status}
                </span>
                {caseData.is_urgent && (
                  <span
                    style={{
                      fontSize: "0.8rem",
                      fontWeight: "700",
                      background: "var(--danger)",
                      color: "#ffffff",
                      padding: "3px 10px",
                      borderRadius: "12px",
                    }}
                  >
                    Urgent
                  </span>
                )}
                <span
                  style={{
                    fontSize: "0.8rem",
                    fontWeight: "700",
                    background: "var(--gold-soft)",
                    color: "#5a4505",
                    padding: "3px 10px",
                    borderRadius: "12px",
                  }}
                >
                  {caseData.district}
                </span>
              </div>
            </div>
            <div style={{ fontSize: "0.82rem", color: "var(--muted)" }}>
              Reported: {new Date(caseData.created_at).toLocaleString()}
            </div>
          </div>

          <div
            style={{
              marginTop: "16px",
              padding: "14px 16px",
              backgroundColor: "#f7faf9",
              borderRadius: "10px",
              border: "1px solid var(--line)",
            }}
          >
            <div style={{ fontSize: "0.8rem", fontWeight: "700", color: "var(--muted)", textTransform: "uppercase" }}>
              Category & Narrative
            </div>
            <div style={{ fontSize: "1.05rem", fontWeight: "700", color: "var(--teal-900)", marginTop: "2px" }}>
              {caseData.category}
            </div>
            <p style={{ marginTop: "8px", fontSize: "0.92rem", lineHeight: "1.55", color: "var(--text)", whiteSpace: "pre-wrap" }}>
              {caseData.description}
            </p>
          </div>
        </div>
      )}

      {/* Location Intelligence Panel (Panchayat removed) */}
      <div className="content-card" style={{ borderTop: "4px solid var(--gold)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px", flexWrap: "wrap", gap: "10px" }}>
          <h2 style={{ fontSize: "1.15rem", fontWeight: "800", color: "var(--teal-900)" }}>
            Case Location Intelligence
          </h2>
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: "700",
              background: "var(--gold-soft)",
              color: "#5a4505",
              border: "1px dashed var(--gold)",
              padding: "3px 8px",
              borderRadius: "6px",
            }}
          >
            SIMULATED PROTOTYPE
          </span>
        </div>

        <div
          style={{
            fontSize: "0.8rem",
            color: "var(--teal-900)",
            backgroundColor: "#edf5f3",
            padding: "8px 12px",
            borderRadius: "6px",
            marginBottom: "14px",
            border: "1px solid var(--line)",
          }}
        >
          Audit Trail Notice: Reviewing this location is recorded in the case history (event: <code>location_viewed</code>).
        </div>

        {locationData ? (
          <div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                gap: "14px",
                marginBottom: "14px",
              }}
            >
              <div>
                <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>District:</span>{" "}
                <strong>{locationData.district}</strong>
              </div>
              <div>
                <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Citizen Consent:</span>{" "}
                <strong style={{ color: locationData.location_consent ? "#137333" : "var(--muted)" }}>
                  {locationData.location_consent ? "Granted (~1 km)" : "Declined"}
                </strong>
              </div>
            </div>

            {locationData.location_text && (
              <div
                style={{
                  marginBottom: "14px",
                  padding: "10px 14px",
                  backgroundColor: "#f7faf9",
                  borderRadius: "8px",
                  border: "1px solid var(--line)",
                }}
              >
                <span style={{ color: "var(--muted)", fontSize: "0.85rem" }}>Landmark / Area:</span>{" "}
                <strong>{locationData.location_text}</strong>
              </div>
            )}

            {locationData.approx_lat !== null && locationData.approx_lng !== null ? (
              <div
                style={{
                  backgroundColor: "#eff7f5",
                  border: "1px solid #bfdbd8",
                  padding: "14px",
                  borderRadius: "8px",
                }}
              >
                <div style={{ fontSize: "0.9rem", color: "var(--teal-900)", fontWeight: "700" }}>
                  Approximate Coordinates (Rounded ~1 km): {locationData.approx_lat.toFixed(2)}° N, {locationData.approx_lng.toFixed(2)}° E
                </div>
                <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: "4px" }}>
                  Raw coordinates are purged server-side to protect citizen privacy. Subject to 90-day retention cleanup.
                </div>
              </div>
            ) : (
              <div style={{ color: "var(--muted)", fontSize: "0.85rem", fontStyle: "italic" }}>
                No GPS coordinates were shared for this case.
              </div>
            )}
          </div>
        ) : (
          <div style={{ color: "var(--muted)" }}>No location record available for this case.</div>
        )}
      </div>

      {/* Simulated VoIP Call Sessions Panel */}
      <div className="content-card" style={{ borderTop: "4px solid var(--teal-900)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", flexWrap: "wrap", gap: "8px" }}>
          <h2 style={{ fontSize: "1.15rem", fontWeight: "800", color: "var(--teal-900)" }}>
            In-App Voice Call Session
          </h2>
          <span
            style={{
              fontSize: "0.75rem",
              fontWeight: "700",
              background: "var(--gold-soft)",
              color: "#5a4505",
              border: "1px dashed var(--gold)",
              padding: "3px 8px",
              borderRadius: "6px",
            }}
          >
            SIMULATED PROTOTYPE
          </span>
        </div>

        <div
          style={{
            border: "1px dashed var(--gold)",
            background: "var(--gold-soft)",
            color: "#5a4505",
            borderRadius: "8px",
            padding: "8px 12px",
            fontSize: "0.82rem",
            marginBottom: "14px",
          }}
        >
          Simulated prototype call. No real helpline or emergency authority is contacted. No voice audio is recorded or stored.
        </div>

        {callNotice && (
          <div
            style={{
              background: "#edf5f3",
              color: "var(--teal-900)",
              border: "1px solid var(--line)",
              padding: "10px 14px",
              borderRadius: "8px",
              fontSize: "0.85rem",
              marginBottom: "14px",
            }}
          >
            {callNotice}
          </div>
        )}

        {/* Active Call Box */}
        {activeCall ? (
          <div
            style={{
              backgroundColor: "#f0fdf4",
              border: "1.5px solid #86efac",
              padding: "16px",
              borderRadius: "10px",
              marginBottom: "16px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
              <div style={{ fontSize: "1rem", color: "#166534", fontWeight: "800" }}>
                Call Status: {activeCall.status.toUpperCase()}
              </div>
              {activeCall.status === "connected" && (
                <div
                  style={{
                    backgroundColor: "#166534",
                    color: "#ffffff",
                    padding: "4px 12px",
                    borderRadius: "6px",
                    fontWeight: "700",
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.95rem",
                  }}
                >
                  {formatTimer(callDuration)}
                </div>
              )}
            </div>

            <div style={{ display: "flex", gap: "10px" }}>
              {activeCall.status === "ringing" && (
                <button
                  type="button"
                  className="btn btn-primary"
                  style={{ minHeight: "40px", fontSize: "0.88rem", width: "auto", background: "#10b981" }}
                  onClick={() => handleAcceptCall(activeCall.id)}
                  disabled={callActionLoading}
                >
                  Accept Call
                </button>
              )}
              {["requested", "ringing", "connected"].includes(activeCall.status) && (
                <button
                  type="button"
                  className="btn btn-danger"
                  style={{ minHeight: "40px", fontSize: "0.88rem", width: "auto" }}
                  onClick={() => handleEndCall(activeCall.id)}
                  disabled={callActionLoading}
                >
                  End Call
                </button>
              )}
            </div>
          </div>
        ) : (
          <div style={{ marginBottom: "16px" }}>
            <button
              type="button"
              className="btn btn-primary"
              style={{ width: "auto", minHeight: "42px", fontSize: "0.9rem" }}
              onClick={handleStartCall}
              disabled={callActionLoading}
            >
              {callActionLoading ? "Initiating Call..." : "Call Reporter (Simulated)"}
            </button>
            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                fontSize: "0.82rem",
                color: "var(--muted)",
                marginTop: "8px",
                cursor: "pointer",
              }}
            >
              <input
                type="checkbox"
                checked={overrideSolved}
                onChange={(e) => setOverrideSolved(e.target.checked)}
              />
              Override if case is Solved (audited to case history)
            </label>
          </div>
        )}

        {/* Historical Calls */}
        {callsData.length > 0 && (
          <div style={{ borderTop: "1px solid var(--line)", paddingTop: "14px", marginTop: "14px" }}>
            <h3 style={{ fontSize: "0.9rem", fontWeight: "700", color: "var(--text)", marginBottom: "8px" }}>
              Recorded Call Sessions ({callsData.length})
            </h3>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem" }}>
                <thead>
                  <tr style={{ borderBottom: "1.5px solid var(--line)", textAlign: "left", color: "var(--muted)" }}>
                    <th style={{ padding: "8px" }}>Call ID</th>
                    <th style={{ padding: "8px" }}>Requested By</th>
                    <th style={{ padding: "8px" }}>Status</th>
                    <th style={{ padding: "8px" }}>Duration</th>
                    <th style={{ padding: "8px" }}>End Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {callsData.map((c) => (
                    <tr key={c.id} style={{ borderBottom: "1px solid var(--line)" }}>
                      <td style={{ padding: "8px", fontFamily: "var(--font-mono)" }}>#{c.id}</td>
                      <td style={{ padding: "8px" }}>{c.requested_by}</td>
                      <td style={{ padding: "8px" }}>{c.status}</td>
                      <td style={{ padding: "8px" }}>{c.duration_seconds !== null ? `${c.duration_seconds}s` : "-"}</td>
                      <td style={{ padding: "8px" }}>{c.end_reason || "-"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* AI Decision-Support Summary */}
      <div className="content-card" style={{ borderTop: "4px solid #8b5cf6" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px", flexWrap: "wrap", gap: "8px" }}>
          <h2 style={{ fontSize: "1.15rem", fontWeight: "800", color: "var(--teal-900)" }}>
            AI Decision-Support Assistance
          </h2>
          <span style={{ fontSize: "0.75rem", fontWeight: "700", background: "#ede9fe", color: "#6d28d9", padding: "3px 8px", borderRadius: "6px" }}>
            ADVISORY ONLY
          </span>
        </div>
        <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginBottom: "12px" }}>
          AI never decides abuse, guilt, or risk. Human officers retain exclusive decision authority.
        </p>

        {aiSummary ? (
          <div style={{ backgroundColor: "#fbfafc", border: "1px solid #ddd6fe", padding: "16px", borderRadius: "8px" }}>
            <div style={{ fontSize: "0.8rem", color: "#7c3aed", fontWeight: "700", marginBottom: "8px" }}>
              {aiSummary.disclaimer}
            </div>
            <div style={{ fontWeight: "700", fontSize: "0.95rem", color: "var(--teal-900)", marginTop: "10px" }}>
              Structured Summary:
            </div>
            <p style={{ fontSize: "0.9rem", color: "var(--text)", marginTop: "4px", lineHeight: "1.55" }}>
              {aiSummary.structured_summary}
            </p>

            <div style={{ fontWeight: "700", fontSize: "0.95rem", color: "var(--teal-900)", marginTop: "14px" }}>
              Information Gaps Checklist:
            </div>
            <ul style={{ paddingLeft: "20px", fontSize: "0.88rem", color: "var(--muted)", marginTop: "4px" }}>
              {aiSummary.missing_information?.map((m, i) => (
                <li key={i}>{m}</li>
              ))}
            </ul>
          </div>
        ) : (
          <button
            type="button"
            className="btn btn-secondary"
            style={{ width: "auto", minHeight: "38px", fontSize: "0.85rem" }}
            onClick={handleRequestAiSummary}
            disabled={aiLoading}
          >
            {aiLoading ? "Generating AI Summary..." : "Generate AI Decision Support Summary"}
          </button>
        )}
      </div>

      {/* Chronological Case History Audit Trail */}
      <div className="content-card">
        <h2 style={{ fontSize: "1.15rem", fontWeight: "800", color: "var(--teal-900)", marginBottom: "4px" }}>
          Chronological Case Audit Trail
        </h2>
        <p style={{ fontSize: "0.85rem", color: "var(--muted)", marginBottom: "16px" }}>
          Tamper-evident operational audit trail. Citizen narratives and exact coordinates are strictly omitted from logs.
        </p>

        {historyData.length === 0 ? (
          <div style={{ color: "var(--muted)", fontSize: "0.9rem" }}>No audit events recorded yet.</div>
        ) : (
          <div style={{ borderLeft: "2px solid var(--teal-700)", paddingLeft: "16px", marginLeft: "8px" }}>
            {historyData.map((item, idx) => (
              <div key={item.id || idx} style={{ marginBottom: "16px", position: "relative" }}>
                <div
                  style={{
                    position: "absolute",
                    left: "-22px",
                    top: "4px",
                    width: "10px",
                    height: "10px",
                    borderRadius: "50%",
                    backgroundColor: "var(--teal-700)",
                  }}
                />
                <div style={{ fontSize: "0.92rem", fontWeight: "700", color: "var(--text)" }}>
                  {item.action}
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--muted)", marginTop: "2px" }}>
                  {item.details}
                </div>
                <div style={{ fontSize: "0.78rem", color: "var(--muted)", marginTop: "2px" }}>
                  {item.actor_name ? `By: ${item.actor_name} | ` : ""}
                  {new Date(item.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
