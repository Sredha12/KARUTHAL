import React, { useState, useEffect, useRef } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * CallPanel.jsx
 *
 * Full-featured in-app VoIP call management and signalling panel.
 * - Supports both Officer (Bearer token) and Citizen Reporter (X-Reporter-Token).
 * - Enforces state machine: requested -> ringing -> connected -> ended.
 * - Authenticates WebSocket signalling with single-use tickets (POST /ws-ticket).
 * - Displays mandatory prototype notices and timer during active calls.
 */
export default function CallPanel({
  caseId,
  role = "officer", // "officer" | "reporter"
  authToken, // JWT token if officer
  reporterToken, // Token from sessionStorage if reporter
}) {
  const [activeCall, setActiveCall] = useState(null);
  const [callsList, setCallsList] = useState([]);
  const [callDuration, setCallDuration] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [overrideSolved, setOverrideSolved] = useState(false);

  const wsRef = useRef(null);
  const timerRef = useRef(null);

  // Helper headers based on role
  const getHeaders = () => {
    const headers = { "Content-Type": "application/json" };
    if (role === "officer" && authToken) {
      headers["Authorization"] = `Bearer ${authToken}`;
    } else if (role === "reporter" && reporterToken) {
      headers["X-Reporter-Token"] = reporterToken;
    }
    return headers;
  };

  // Poll call session status
  const loadCalls = async () => {
    if (!caseId) return;
    try {
      if (role === "officer") {
        const res = await fetch(`${API_BASE_URL}/api/cases/${caseId}/calls`, {
          headers: getHeaders(),
        });
        if (res.ok) {
          const data = await res.json();
          setCallsList(data.calls || []);
          // Check for in-progress session
          const ongoing = data.calls.find((c) =>
            ["requested", "ringing", "connected"].includes(c.status)
          );
          setActiveCall(ongoing || null);
        }
      }
    } catch (err) {
      console.error("Failed to load calls:", err);
    }
  };

  useEffect(() => {
    loadCalls();
    const interval = setInterval(loadCalls, 4000);
    return () => clearInterval(interval);
  }, [caseId, role]);

  // Call duration timer
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

  // Connect WebSocket signalling with single-use ticket
  const connectSignalling = async (callId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/calls/${callId}/ws-ticket`, {
        method: "POST",
        headers: getHeaders(),
      });
      if (!res.ok) return;
      const data = await res.json();
      const ticket = data.ticket;

      const wsUrl = `${API_BASE_URL.replace(/^http/, "ws")}/api/calls/${callId}/signal?ticket=${ticket}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => console.log("[VoIP Signalling] Connected to call room", callId);
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        console.log("[VoIP Signalling Message]", msg);
      };
      ws.onclose = () => console.log("[VoIP Signalling] Disconnected");
      wsRef.current = ws;
    } catch (err) {
      console.error("Failed to initialize signalling:", err);
    }
  };

  // 1. Citizen requests callback
  const handleRequestCallback = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/reports/${caseId}/callback-request`, {
        method: "POST",
        headers: getHeaders(),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Failed to request callback.");
      setActiveCall(data.call);
      connectSignalling(data.call.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 2. Officer starts call
  const handleOfficerStartCall = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/cases/${caseId}/calls`, {
        method: "POST",
        headers: getHeaders(),
        body: JSON.stringify({ override_solved: overrideSolved }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Failed to initiate call.");
      setActiveCall(data.call);
      connectSignalling(data.call.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 3. Accept incoming call
  const handleAcceptCall = async (callId) => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE_URL}/api/calls/${callId}/accept`, {
        method: "POST",
        headers: getHeaders(),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Failed to accept call.");
      setActiveCall(data.call);
      connectSignalling(callId);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 4. Decline call
  const handleDeclineCall = async (callId) => {
    try {
      await fetch(`${API_BASE_URL}/api/calls/${callId}/decline`, {
        method: "POST",
        headers: getHeaders(),
      });
      if (wsRef.current) wsRef.current.close();
      setActiveCall(null);
      loadCalls();
    } catch (err) {
      console.error(err);
    }
  };

  // 5. End call
  const handleEndCall = async (callId) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/calls/${callId}/end`, {
        method: "POST",
        headers: getHeaders(),
      });
      if (wsRef.current) wsRef.current.close();
      const data = await res.json();
      setActiveCall(null);
      loadCalls();
    } catch (err) {
      console.error(err);
    }
  };

  const formatTimer = (seconds) => {
    const m = Math.floor(seconds / 60)
      .toString()
      .padStart(2, "0");
    const s = (seconds % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <h4 style={styles.title}>Voice Call Sessions (Prototype Voice Channel)</h4>
        <span style={styles.badge}>SIMULATED PROTOTYPE</span>
      </div>

      <div style={styles.disclaimerNotice}>
        Notice: Simulated prototype call. No real helpline or emergency authority is contacted. No voice
        audio is recorded or stored.
      </div>

      {error && <div style={styles.errorBox}>{error}</div>}

      {/* Active Session Display */}
      {activeCall ? (
        <div style={styles.activeCallContainer}>
          <div style={styles.statusRow}>
            <span>Status: </span>
            <span style={styles.statusHighlight}>{activeCall.status.toUpperCase()}</span>
            {activeCall.status === "connected" && (
              <span style={styles.timerBadge}>{formatTimer(callDuration)}</span>
            )}
          </div>

          <div style={styles.actionRow}>
            {activeCall.status === "ringing" && (
              <>
                <button
                  style={styles.btnSuccess}
                  onClick={() => handleAcceptCall(activeCall.id)}
                  disabled={loading}
                >
                  Accept Call
                </button>
                <button
                  style={styles.btnDanger}
                  onClick={() => handleDeclineCall(activeCall.id)}
                >
                  Decline
                </button>
              </>
            )}

            {activeCall.status === "connected" && (
              <button
                style={styles.btnDanger}
                onClick={() => handleEndCall(activeCall.id)}
              >
                End Call
              </button>
            )}

            {activeCall.status === "requested" && role === "officer" && (
              <button
                style={styles.btnPrimary}
                onClick={handleOfficerStartCall}
                disabled={loading}
              >
                Ring Reporter Now
              </button>
            )}

            {activeCall.status === "requested" && role === "reporter" && (
              <div style={styles.waitingNote}>
                Callback requested. Waiting for district officer to initiate ringing...
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Inactive State: Start or Request Options */
        <div style={styles.idleContainer}>
          {role === "reporter" ? (
            <button
              style={styles.btnPrimary}
              onClick={handleRequestCallback}
              disabled={loading || !reporterToken}
            >
              Request Voice Callback from District Officer
            </button>
          ) : (
            <div style={styles.officerInitiateBox}>
              <button
                style={styles.btnPrimary}
                onClick={handleOfficerStartCall}
                disabled={loading}
              >
                Initiate Outbound Call to Reporter
              </button>
              <label style={styles.overrideLabel}>
                <input
                  type="checkbox"
                  checked={overrideSolved}
                  onChange={(e) => setOverrideSolved(e.target.checked)}
                />
                Override if case is Solved (logged to audit trail)
              </label>
            </div>
          )}
        </div>
      )}

      {/* Historical Calls List (for Officer) */}
      {role === "officer" && callsList.length > 0 && (
        <div style={styles.historySection}>
          <h5 style={styles.historyTitle}>Case Call History</h5>
          <table style={styles.table}>
            <thead>
              <tr style={styles.thRow}>
                <th style={styles.th}>ID</th>
                <th style={styles.th}>Requested By</th>
                <th style={styles.th}>Status</th>
                <th style={styles.th}>Duration</th>
                <th style={styles.th}>End Reason</th>
              </tr>
            </thead>
            <tbody>
              {callsList.map((c) => (
                <tr key={c.id} style={styles.tr}>
                  <td style={styles.td}>#{c.id}</td>
                  <td style={styles.td}>{c.requested_by}</td>
                  <td style={styles.td}>{c.status}</td>
                  <td style={styles.td}>{c.duration_seconds !== null ? `${c.duration_seconds}s` : "-"}</td>
                  <td style={styles.td}>{c.end_reason || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const styles = {
  card: {
    backgroundColor: "#ffffff",
    border: "1px solid #e2e8f0",
    borderRadius: "8px",
    padding: "16px",
    marginTop: "16px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "8px",
  },
  title: {
    margin: 0,
    fontSize: "15px",
    fontWeight: "600",
    color: "#0f172a",
  },
  badge: {
    backgroundColor: "#fef3c7",
    color: "#92400e",
    fontSize: "11px",
    fontWeight: "700",
    padding: "3px 8px",
    borderRadius: "12px",
    border: "1px solid #fde68a",
  },
  disclaimerNotice: {
    backgroundColor: "#f8fafc",
    borderLeft: "3px solid #eab308",
    padding: "8px 12px",
    fontSize: "12px",
    color: "#713f12",
    marginBottom: "14px",
    borderRadius: "4px",
  },
  errorBox: {
    backgroundColor: "#fef2f2",
    border: "1px solid #fecaca",
    color: "#b91c1c",
    padding: "8px",
    borderRadius: "6px",
    fontSize: "12px",
    marginBottom: "12px",
  },
  activeCallContainer: {
    backgroundColor: "#f0fdf4",
    border: "1px solid #bbf7d0",
    borderRadius: "6px",
    padding: "14px",
    marginBottom: "14px",
  },
  statusRow: {
    fontSize: "14px",
    color: "#166534",
    fontWeight: "500",
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "12px",
  },
  statusHighlight: {
    fontWeight: "700",
    backgroundColor: "#dcfce7",
    padding: "2px 8px",
    borderRadius: "4px",
  },
  timerBadge: {
    backgroundColor: "#166534",
    color: "#ffffff",
    padding: "2px 8px",
    borderRadius: "4px",
    fontSize: "12px",
    fontWeight: "700",
  },
  actionRow: {
    display: "flex",
    gap: "10px",
  },
  idleContainer: {
    marginBottom: "14px",
  },
  btnPrimary: {
    backgroundColor: "#2563eb",
    color: "#ffffff",
    border: "none",
    padding: "8px 14px",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: "500",
    cursor: "pointer",
  },
  btnSuccess: {
    backgroundColor: "#16a34a",
    color: "#ffffff",
    border: "none",
    padding: "8px 14px",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: "500",
    cursor: "pointer",
  },
  btnDanger: {
    backgroundColor: "#dc2626",
    color: "#ffffff",
    border: "none",
    padding: "8px 14px",
    borderRadius: "6px",
    fontSize: "13px",
    fontWeight: "500",
    cursor: "pointer",
  },
  waitingNote: {
    fontSize: "13px",
    color: "#475569",
    fontStyle: "italic",
  },
  officerInitiateBox: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  overrideLabel: {
    fontSize: "12px",
    color: "#64748b",
    display: "flex",
    alignItems: "center",
    gap: "6px",
    cursor: "pointer",
  },
  historySection: {
    marginTop: "16px",
    borderTop: "1px solid #f1f5f9",
    paddingTop: "12px",
  },
  historyTitle: {
    margin: "0 0 8px 0",
    fontSize: "13px",
    color: "#334155",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "12px",
  },
  thRow: {
    backgroundColor: "#f8fafc",
    textAlign: "left",
  },
  th: {
    padding: "6px 8px",
    borderBottom: "1px solid #e2e8f0",
    color: "#64748b",
  },
  tr: {
    borderBottom: "1px solid #f1f5f9",
  },
  td: {
    padding: "6px 8px",
    color: "#334155",
  },
};
