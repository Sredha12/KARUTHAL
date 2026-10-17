import React, { useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const SERVICES = [
  "Child Welfare Committee (CWC)",
  "District Child Protection Unit (DCPU)",
  "Child Guidance Clinic (Mental Health)",
  "District Medical Office / Taluk Hospital",
  "Special Juvenile Police Unit (SJPU)",
  "Educational Support Services",
  "Shelter / Specialized Adoption Agency",
];

export default function ReferralForm({ caseId, token, onReferralCreated }) {
  const [service, setService] = useState(SERVICES[0]);
  const [urgency, setUrgency] = useState("Standard");
  const [nextAction, setNextAction] = useState("");
  const [followUpDue, setFollowUpDue] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [resultNotice, setResultNotice] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResultNotice(null);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE_URL}/api/cases/${caseId}/referrals`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          service,
          urgency,
          next_action: nextAction.trim(),
          follow_up_due: followUpDue ? new Date(followUpDue).toISOString() : null,
          notes: notes.trim(),
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Failed to create referral.");

      setResultNotice(data);
      if (onReferralCreated) onReferralCreated(data.referral);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 540, padding: 16, border: "1px solid #e5e7eb", borderRadius: 8, fontFamily: "system-ui, sans-serif" }}>
      <h3 style={{ marginTop: 0 }}>Initiate Multi-Agency Service Referral: {caseId}</h3>
      <div style={{ padding: 10, background: "#fef3c7", border: "1px solid #f59e0b", borderRadius: 6, fontSize: "0.85rem", color: "#92400e", marginBottom: 14 }}>
        <strong>Important Legal Notice:</strong> Logging this referral records an internal coordination record. It does NOT automatically transmit notifications to external agencies or CWC. Authorized human contact is required.
      </div>

      {error && (
        <div style={{ padding: 10, background: "#fee2e2", color: "#b91c1c", borderRadius: 4, marginBottom: 12 }}>
          {error}
        </div>
      )}

      {resultNotice ? (
        <div style={{ padding: 12, background: "#ecfdf5", border: "1px solid #10b981", borderRadius: 6 }}>
          <h4 style={{ margin: "0 0 6px 0", color: "#065f46" }}>Referral Record Created</h4>
          <p style={{ margin: 0, fontSize: "0.9rem" }}>Target Service: <strong>{resultNotice.referral.serviceLinkage.service}</strong></p>
          <p style={{ fontSize: "0.85rem", color: "#047857", marginTop: 4 }}>
            {resultNotice.disclaimer}
          </p>
          <button
            onClick={() => setResultNotice(null)}
            style={{ marginTop: 8, padding: "6px 12px", background: "#059669", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}
          >
            Create Another Referral
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div>
            <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>Target Support Service *</label>
            <select
              value={service}
              onChange={(e) => setService(e.target.value)}
              style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
            >
              {SERVICES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>Urgency Classification *</label>
            <select
              value={urgency}
              onChange={(e) => setUrgency(e.target.value)}
              style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
            >
              <option value="Low">Low (Long-term support)</option>
              <option value="Standard">Standard (Within 72 hours)</option>
              <option value="Urgent">Urgent (Within 24 hours)</option>
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>Next Action Required</label>
            <input
              type="text"
              value={nextAction}
              onChange={(e) => setNextAction(e.target.value)}
              placeholder="e.g. Convene preliminary CWC review panel"
              style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>Follow-up Due Date</label>
            <input
              type="date"
              value={followUpDue}
              onChange={(e) => setFollowUpDue(e.target.value)}
              style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>Coordination Directives (max 500 chars)</label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Operational details for caseworker coordination..."
              style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: "10px 16px",
              background: loading ? "#9ca3af" : "#7c3aed",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Recording Referral..." : "Register Service Referral"}
          </button>
        </form>
      )}
    </div>
  );
}
