import React, { useState, useEffect } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

/**
 * DistrictCaseMap.jsx
 *
 * Lightweight, zero-dependency GeoJSON map component for district officers.
 * - Consumes `GET /api/dashboard/map?district={district}`.
 * - Does NOT require Google Maps or Mapbox API keys.
 * - Plots approximate case coordinates (~1 km resolution) within the district container.
 * - Emphasizes privacy: no reporter names, contacts, or exact street pins.
 */
export default function DistrictCaseMap({ district = "Thiruvananthapuram", authToken, onSelectCase }) {
  const [geoData, setGeoData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedFeature, setSelectedFeature] = useState(null);

  useEffect(() => {
    if (!district || !authToken) return;

    setLoading(true);
    setError("");

    fetch(`${API_BASE_URL}/api/dashboard/map?district=${encodeURIComponent(district)}`, {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    })
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.message || `Failed to load map data (${res.status})`);
        }
        return res.json();
      })
      .then((data) => {
        setGeoData(data);
      })
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [district, authToken]);

  if (loading) {
    return (
      <div style={styles.card}>
        <div style={styles.centerText}>Loading {district} district map points...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.card}>
        <div style={styles.errorText}>
          <strong>Map Error:</strong> {error}
        </div>
      </div>
    );
  }

  const features = geoData?.features || [];

  // Approximate normalization for visual placement within canvas (Kerala bounds: 8.1 - 12.9 N, 74.8 - 77.5 E)
  // Maps coordinates to percentage (0 - 100%) inside container
  const getPositionPercent = (coords) => {
    const [lng, lat] = coords;
    // Kerala bounding box
    const minLat = 8.1;
    const maxLat = 12.9;
    const minLng = 74.8;
    const maxLng = 77.5;

    const x = ((lng - minLng) / (maxLng - minLng)) * 100;
    const y = (1 - (lat - minLat) / (maxLat - minLat)) * 100; // Invert latitude for screen Y
    return { left: `${Math.min(95, Math.max(5, x))}%`, top: `${Math.min(95, Math.max(5, y))}%` };
  };

  return (
    <div style={styles.card}>
      <div style={styles.header}>
        <div>
          <h3 style={styles.title}>District Case Distribution Map ({district})</h3>
          <p style={styles.subtitle}>
            Displaying {features.length} consented case location(s) rounded to ~1 km resolution.
          </p>
        </div>
        <span style={styles.badge}>SIMULATED PROTOTYPE (NO KEYS)</span>
      </div>

      {/* Map Canvas Visualizer */}
      <div style={styles.mapContainer}>
        {/* Stylized background grid simulating district boundary */}
        <div style={styles.gridOverlay}>
          <div style={styles.watermark}>KERALA STATE MAP CONTAINER - {district.toUpperCase()}</div>
        </div>

        {features.length === 0 ? (
          <div style={styles.emptyMapNote}>
            No consented coordinates found for active cases in {district}.
          </div>
        ) : (
          features.map((f, idx) => {
            const pos = getPositionPercent(f.geometry.coordinates);
            const isUrgent = f.properties.is_urgent;
            const isSelected = selectedFeature?.properties?.report_id === f.properties.report_id;

            return (
              <div
                key={f.properties.report_id || idx}
                onClick={() => setSelectedFeature(f)}
                title={`${f.properties.report_id} (${f.properties.panchayat})`}
                style={{
                  ...styles.pin,
                  ...pos,
                  backgroundColor: isUrgent ? "#ef4444" : "#3b82f6",
                  transform: isSelected ? "translate(-50%, -50%) scale(1.4)" : "translate(-50%, -50%)",
                  boxShadow: isSelected ? "0 0 0 4px rgba(59, 130, 246, 0.4)" : "0 1px 3px rgba(0,0,0,0.3)",
                }}
              >
                <div style={styles.pinDot} />
              </div>
            );
          })
        )}
      </div>

      {/* Selected Case Quick-Detail Popup */}
      {selectedFeature && (
        <div style={styles.detailPopup}>
          <div style={styles.popupHeader}>
            <strong style={styles.popupCaseId}>{selectedFeature.properties.report_id}</strong>
            <button style={styles.closeBtn} onClick={() => setSelectedFeature(null)}>
              ×
            </button>
          </div>
          <div style={styles.popupBody}>
            <div>
              <strong>Panchayat:</strong> {selectedFeature.properties.panchayat}
            </div>
            <div>
              <strong>Status:</strong> {selectedFeature.properties.status}
            </div>
            <div>
              <strong>Coordinates:</strong> {selectedFeature.geometry.coordinates[1].toFixed(2)} N,{" "}
              {selectedFeature.geometry.coordinates[0].toFixed(2)} E (~1 km precision)
            </div>
            {selectedFeature.properties.is_urgent && (
              <span style={styles.urgentTag}>Urgent Case</span>
            )}
          </div>
          {onSelectCase && (
            <button
              style={styles.openCaseBtn}
              onClick={() => onSelectCase(selectedFeature.properties.report_id)}
            >
              Open Full Case File
            </button>
          )}
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
    marginBottom: "20px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "12px",
  },
  title: {
    margin: 0,
    fontSize: "16px",
    fontWeight: "600",
    color: "#0f172a",
  },
  subtitle: {
    margin: "4px 0 0 0",
    fontSize: "12px",
    color: "#64748b",
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
  mapContainer: {
    position: "relative",
    width: "100%",
    height: "260px",
    backgroundColor: "#f1f5f9",
    borderRadius: "6px",
    overflow: "hidden",
    border: "1px solid #cbd5e1",
  },
  gridOverlay: {
    width: "100%",
    height: "100%",
    backgroundImage: "radial-gradient(#94a3b8 1px, transparent 1px)",
    backgroundSize: "20px 20px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  watermark: {
    fontSize: "13px",
    fontWeight: "700",
    color: "#cbd5e1",
    letterSpacing: "1px",
    userSelect: "none",
  },
  emptyMapNote: {
    position: "absolute",
    top: "50%",
    left: "50%",
    transform: "translate(-50%, -50%)",
    fontSize: "13px",
    color: "#64748b",
    fontStyle: "italic",
    textAlign: "center",
  },
  pin: {
    position: "absolute",
    width: "16px",
    height: "16px",
    borderRadius: "50%",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "transform 0.15s ease",
    zIndex: 10,
  },
  pinDot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    backgroundColor: "#ffffff",
  },
  detailPopup: {
    marginTop: "12px",
    backgroundColor: "#f8fafc",
    border: "1px solid #e2e8f0",
    borderRadius: "6px",
    padding: "12px",
  },
  popupHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "6px",
  },
  popupCaseId: {
    fontSize: "14px",
    color: "#0f172a",
  },
  closeBtn: {
    background: "none",
    border: "none",
    fontSize: "18px",
    cursor: "pointer",
    color: "#64748b",
  },
  popupBody: {
    fontSize: "12px",
    color: "#334155",
    lineHeight: "1.6",
  },
  urgentTag: {
    display: "inline-block",
    marginTop: "4px",
    fontSize: "11px",
    fontWeight: "600",
    color: "#b91c1c",
    backgroundColor: "#fee2e2",
    padding: "2px 6px",
    borderRadius: "4px",
  },
  openCaseBtn: {
    marginTop: "10px",
    backgroundColor: "#2563eb",
    color: "#ffffff",
    border: "none",
    padding: "6px 12px",
    borderRadius: "4px",
    fontSize: "12px",
    cursor: "pointer",
  },
  centerText: {
    textAlign: "center",
    padding: "20px",
    fontSize: "13px",
    color: "#64748b",
  },
  errorText: {
    color: "#dc2626",
    fontSize: "13px",
  },
};
