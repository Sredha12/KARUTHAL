import React, { useState } from "react";

/**
 * ReporterLocationPicker.jsx
 *
 * Privacy-preserving location selector for citizen reports in Kerala.
 * - Enforces explicit consent checkbox before saving coordinates.
 * - Informs reporter of 2-decimal-place rounding (~1 km precision) and 90-day retention.
 * - Validates bounding box for Kerala (Lat 8.1 - 12.9, Lng 74.8 - 77.5).
 */
export default function ReporterLocationPicker({ value = {}, onChange }) {
  const [locationText, setLocationText] = useState(value.location_text || "");
  const [ward, setWard] = useState(value.ward || "");
  const [consent, setConsent] = useState(value.location_consent || false);
  const [lat, setLat] = useState(value.approx_lat || null);
  const [lng, setLng] = useState(value.approx_lng || null);
  const [source, setSource] = useState(value.location_source || "typed");
  const [geoError, setGeoError] = useState("");
  const [detecting, setDetecting] = useState(false);

  const notifyChange = (updated) => {
    if (onChange) {
      onChange({
        location_text: updated.locationText !== undefined ? updated.locationText : locationText,
        ward: updated.ward !== undefined ? updated.ward : ward,
        location_consent: updated.consent !== undefined ? updated.consent : consent,
        approx_lat: updated.consent === false ? null : (updated.lat !== undefined ? updated.lat : lat),
        approx_lng: updated.consent === false ? null : (updated.lng !== undefined ? updated.lng : lng),
        location_source: updated.source || source,
      });
    }
  };

  const handleLocationTextChange = (e) => {
    const val = e.target.value.slice(0, 200);
    setLocationText(val);
    notifyChange({ locationText: val });
  };

  const handleWardChange = (e) => {
    const val = e.target.value;
    setWard(val);
    notifyChange({ ward: val });
  };

  const handleConsentToggle = (e) => {
    const checked = e.target.checked;
    setConsent(checked);
    if (!checked) {
      setLat(null);
      setLng(null);
      notifyChange({ consent: false, lat: null, lng: null });
    } else {
      notifyChange({ consent: true });
    }
  };

  const handleDeviceLocation = () => {
    setGeoError("");
    if (!consent) {
      setGeoError("Please check the location consent box before requesting device coordinates.");
      return;
    }

    if (!navigator.geolocation) {
      setGeoError("Geolocation is not supported by your browser.");
      return;
    }

    setDetecting(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setDetecting(false);
        const rawLat = pos.coords.latitude;
        const rawLng = pos.coords.longitude;

        // Bounding box validation for Kerala
        if (rawLat < 8.1 || rawLat > 12.9 || rawLng < 74.8 || rawLng > 77.5) {
          setGeoError("Your device coordinates appear to be outside the State of Kerala.");
          return;
        }

        // Preview rounded value
        const roundedLat = parseFloat(rawLat.toFixed(2));
        const roundedLng = parseFloat(rawLng.toFixed(2));

        setLat(roundedLat);
        setLng(roundedLng);
        setSource("device");
        notifyChange({ lat: roundedLat, lng: roundedLng, source: "device", consent: true });
      },
      (err) => {
        setDetecting(false);
        setGeoError(`Unable to retrieve location: ${err.message}`);
      },
      { timeout: 10000, enableHighAccuracy: false }
    );
  };

  const handleClearCoords = () => {
    setLat(null);
    setLng(null);
    setGeoError("");
    notifyChange({ lat: null, lng: null });
  };

  return (
    <div style={styles.card}>
      <h4 style={styles.heading}>Optional Location Details (Privacy Protected)</h4>
      <p style={styles.disclaimer}>
        Exact street coordinates are never published or stored. Any GPS data is rounded to ~1 km
        precision and purged after 90 days.
      </p>

      {/* Free text & Ward */}
      <div style={styles.row}>
        <div style={{ flex: 2, marginRight: "12px" }}>
          <label style={styles.label}>Landmark / Area Description</label>
          <input
            type="text"
            style={styles.input}
            placeholder="e.g. Near Government Primary School, Road Junction"
            value={locationText}
            onChange={handleLocationTextChange}
            maxLength={200}
          />
        </div>
        <div style={{ flex: 1 }}>
          <label style={styles.label}>Ward (Optional)</label>
          <input
            type="text"
            style={styles.input}
            placeholder="e.g. Ward 4"
            value={ward}
            onChange={handleWardChange}
          />
        </div>
      </div>

      {/* Consent Checkbox */}
      <div style={styles.consentBox}>
        <label style={styles.checkboxLabel}>
          <input
            type="checkbox"
            checked={consent}
            onChange={handleConsentToggle}
            style={styles.checkbox}
          />
          <span>
            <strong>I consent</strong> to sharing approximate area coordinates (~1 km resolution) to
            assist child protection officers in locating this concern.
          </span>
        </label>
      </div>

      {/* Device Location Action */}
      {consent && (
        <div style={styles.coordsSection}>
          <div style={styles.buttonRow}>
            <button
              type="button"
              onClick={handleDeviceLocation}
              disabled={detecting}
              style={styles.btnSecondary}
            >
              {detecting ? "Acquiring (~1 km)..." : "Use Approximate Device Location"}
            </button>
            {lat && lng && (
              <button
                type="button"
                onClick={handleClearCoords}
                style={styles.btnDanger}
              >
                Clear Coordinates
              </button>
            )}
          </div>

          {lat && lng && (
            <div style={styles.badgeSuccess}>
              Approximate Coordinates (Rounded): <strong>{lat.toFixed(2)}, {lng.toFixed(2)}</strong> (Source: {source})
            </div>
          )}

          {geoError && <div style={styles.errorText}>{geoError}</div>}
        </div>
      )}
    </div>
  );
}

const styles = {
  card: {
    backgroundColor: "#f8fafc",
    border: "1px solid #e2e8f0",
    borderRadius: "8px",
    padding: "16px",
    marginTop: "16px",
    marginBottom: "16px",
  },
  heading: {
    margin: "0 0 6px 0",
    fontSize: "14px",
    fontWeight: "600",
    color: "#1e293b",
  },
  disclaimer: {
    margin: "0 0 14px 0",
    fontSize: "12px",
    color: "#64748b",
    lineHeight: "1.4",
  },
  row: {
    display: "flex",
    marginBottom: "12px",
  },
  label: {
    display: "block",
    fontSize: "12px",
    fontWeight: "500",
    color: "#475569",
    marginBottom: "4px",
  },
  input: {
    width: "100%",
    padding: "8px 10px",
    fontSize: "13px",
    border: "1px solid #cbd5e1",
    borderRadius: "6px",
    boxSizing: "border-box",
  },
  consentBox: {
    backgroundColor: "#eff6ff",
    border: "1px solid #bfdbfe",
    borderRadius: "6px",
    padding: "10px",
    marginBottom: "12px",
  },
  checkboxLabel: {
    display: "flex",
    alignItems: "flex-start",
    fontSize: "12px",
    color: "#1e3a8a",
    cursor: "pointer",
  },
  checkbox: {
    marginRight: "8px",
    marginTop: "2px",
  },
  coordsSection: {
    marginTop: "10px",
  },
  buttonRow: {
    display: "flex",
    gap: "10px",
    alignItems: "center",
  },
  btnSecondary: {
    backgroundColor: "#ffffff",
    border: "1px solid #cbd5e1",
    color: "#334155",
    padding: "6px 12px",
    borderRadius: "6px",
    fontSize: "12px",
    fontWeight: "500",
    cursor: "pointer",
  },
  btnDanger: {
    backgroundColor: "#fff1f2",
    border: "1px solid #fecdd3",
    color: "#be123c",
    padding: "6px 12px",
    borderRadius: "6px",
    fontSize: "12px",
    cursor: "pointer",
  },
  badgeSuccess: {
    marginTop: "8px",
    fontSize: "12px",
    color: "#15803d",
    backgroundColor: "#f0fdf4",
    border: "1px solid #bbf7d0",
    padding: "6px 10px",
    borderRadius: "4px",
  },
  errorText: {
    marginTop: "8px",
    fontSize: "12px",
    color: "#dc2626",
  },
};
