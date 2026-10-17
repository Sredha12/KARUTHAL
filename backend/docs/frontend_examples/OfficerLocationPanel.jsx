import React, { useState, useEffect } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * OfficerLocationPanel.jsx
 *
 * Displays consented location intelligence to authorized district officers.
 * Automatic audit logging: fetching this endpoint records a 'location_viewed'
 * event in the case chain of custody without leaking coordinates into the audit text.
 */
export default function OfficerLocationPanel({ caseId, authToken }) {
  const [locationData, setLocationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!caseId || !authToken) return;

    setLoading(true);
    setError("");

    fetch(`${API_BASE_URL}/api/cases/${caseId}/location`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    })
      .then(async (res) => {
        if (!res.ok) {
          const errBody = await res.json().catch(() => ({}));
          throw new Error(errBody.message || `Failed with status ${res.status}`);
        }
        return res.json();
      })
      .then((data) => {
        setLocationData(data);
      })
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [caseId, authToken]);

  if (loading) {
    return (
      <div style={styles.card}>
        <div style={styles.loadingText}>Loading case location intelligence...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.card}>
        <div style={styles.errorText}>
          <strong>Access Restricted:</strong> {error}
        </div>
      </div>
    );
  }

  if (!locationData) return null;

  const hasCoords = locationData.approx_lat !== null && locationData.approx_lng !== null;

  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <h4 style={styles.title}>Location & Jurisdiction Details</h4>
        <span style={styles.simulatedBadge}>SIMULATED PROTOTYPE</span>
      </div>

      <div style={styles.auditNotice}>
        Access Logged: Your review of this location was recorded in the case audit trail (action: <code>location_viewed</code>).
      </div>

      <div style={styles.grid}>
        <div style={styles.gridItem}>
          <span style={styles.itemLabel}>Revenue District</span>
          <span style={styles.itemValue}>{locationData.district}</span>
        </div>
        <div style={styles.gridItem}>
          <span style={styles.itemLabel}>Local Body / Panchayat</span>
          <span style={styles.itemValue}>{locationData.panchayat || "Not Specified"}</span>
        </div>
        <div style={styles.gridItem}>
          <span style={styles.itemLabel}>Ward Identifier</span>
          <span style={styles.itemValue}>{locationData.ward || "Not Specified"}</span>
        </div>
        <div style={styles.gridItem}>
          <span style={styles.itemLabel}>Citizen Consent Granted</span>
          <span style={locationData.location_consent ? styles.consentYes : styles.consentNo}>
            {locationData.location_consent ? "Yes (Stored ~1 km resolution)" : "No (Coordinates Dropped)"}
          </span>
        </div>
      </div>

      {locationData.location_text && (
        <div style={styles.textBlock}>
          <span style={styles.itemLabel}>Area Description / Landmark:</span>
          <p style={styles.locationParagraph}>{locationData.location_text}</p>
        </div>
      )}

      {hasCoords ? (
        <div style={styles.coordsBox}>
          <span style={styles.itemLabel}>Approximate Coordinates (~1 km precision):</span>
          <div style={styles.coordsValue}>
            Latitude: <strong>{locationData.approx_lat.toFixed(2)}</strong> | Longitude:{" "}
            <strong>{locationData.approx_lng.toFixed(2)}</strong>
            <span style={styles.sourceTag}>Source: {locationData.location_source}</span>
          </div>
          <small style={styles.coordsNote}>
            Exact coordinates are never retained to safeguard citizen privacy. Subject to 90-day retention policy.
          </small>
        </div>
      ) : (
        <div style={styles.noCoordsBox}>
          No GPS coordinates provided or citizen consent was declined. Rely on district and panchayat jurisdiction.
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
    marginBottom: "10px",
  },
  title: {
    margin: 0,
    fontSize: "15px",
    fontWeight: "600",
    color: "#0f172a",
  },
  simulatedBadge: {
    backgroundColor: "#fef3c7",
    color: "#92400e",
    fontSize: "11px",
    fontWeight: "700",
    padding: "3px 8px",
    borderRadius: "12px",
    border: "1px solid #fde68a",
  },
  auditNotice: {
    fontSize: "11px",
    color: "#475569",
    backgroundColor: "#f8fafc",
    padding: "6px 10px",
    borderRadius: "4px",
    marginBottom: "14px",
    borderLeft: "3px solid #0284c7",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(2, 1fr)",
    gap: "12px",
    marginBottom: "14px",
  },
  gridItem: {
    display: "flex",
    flexDirection: "column",
  },
  itemLabel: {
    fontSize: "11px",
    fontWeight: "600",
    color: "#64748b",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
    marginBottom: "2px",
  },
  itemValue: {
    fontSize: "13px",
    fontWeight: "500",
    color: "#1e293b",
  },
  consentYes: {
    fontSize: "13px",
    fontWeight: "600",
    color: "#16a34a",
  },
  consentNo: {
    fontSize: "13px",
    fontWeight: "500",
    color: "#94a3b8",
  },
  textBlock: {
    backgroundColor: "#f8fafc",
    border: "1px solid #f1f5f9",
    borderRadius: "6px",
    padding: "10px",
    marginBottom: "14px",
  },
  locationParagraph: {
    margin: "4px 0 0 0",
    fontSize: "13px",
    color: "#334155",
    lineHeight: "1.4",
  },
  coordsBox: {
    backgroundColor: "#eff6ff",
    border: "1px solid #dbeafe",
    borderRadius: "6px",
    padding: "10px",
  },
  coordsValue: {
    fontSize: "13px",
    color: "#1e40af",
    marginTop: "2px",
  },
  sourceTag: {
    marginLeft: "10px",
    fontSize: "11px",
    color: "#6b7280",
    backgroundColor: "#ffffff",
    padding: "2px 6px",
    borderRadius: "4px",
    border: "1px solid #cbd5e1",
  },
  coordsNote: {
    display: "block",
    marginTop: "4px",
    fontSize: "11px",
    color: "#64748b",
  },
  noCoordsBox: {
    fontSize: "12px",
    color: "#64748b",
    fontStyle: "italic",
    padding: "8px",
    backgroundColor: "#f8fafc",
    borderRadius: "4px",
  },
  loadingText: {
    fontSize: "13px",
    color: "#64748b",
    fontStyle: "italic",
  },
  errorText: {
    fontSize: "13px",
    color: "#dc2626",
  },
};
