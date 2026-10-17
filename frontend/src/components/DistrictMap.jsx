import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function DistrictMap({ district }) {
  const [geoData, setGeoData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedFeature, setSelectedFeature] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    if (!district) return;
    setLoading(true);
    setError("");

    api.get(`/api/dashboard/map?district=${encodeURIComponent(district)}`)
      .then((data) => setGeoData(data))
      .catch((err) => setError(err.message || "Failed to load district map."))
      .finally(() => setLoading(false));
  }, [district]);

  const features = geoData?.features || [];

  // Kerala bounding box: Lat 8.1 - 12.9, Lng 74.8 - 77.5
  // Map to SVG coordinates (width 600, height 260)
  const projectCoords = (coords) => {
    const [lng, lat] = coords;
    const minLat = 8.1;
    const maxLat = 12.9;
    const minLng = 74.8;
    const maxLng = 77.5;

    const x = ((lng - minLng) / (maxLng - minLng)) * 560 + 20;
    const y = (1 - (lat - minLat) / (maxLat - minLat)) * 220 + 20;
    return { x, y };
  };

  return (
    <div className="content-card" style={{ marginBottom: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px", flexWrap: "wrap", gap: "10px" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1.1rem", fontWeight: "800", color: "var(--teal-900)" }}>
            District Case Location Map ({district})
          </h3>
          <p style={{ margin: "4px 0 0 0", fontSize: "0.85rem", color: "var(--muted)" }}>
            Showing {features.length} consented case location(s) rounded to ~1 km precision.
          </p>
        </div>
        <span
          style={{
            fontSize: "0.78rem",
            fontWeight: "700",
            background: "var(--gold-soft)",
            color: "#5a4505",
            border: "1px dashed var(--gold)",
            padding: "4px 10px",
            borderRadius: "6px",
          }}
        >
          SIMULATED PROTOTYPE (NO REAL KEYS)
        </span>
      </div>

      {loading && (
        <div style={{ padding: "30px", textAlign: "center", color: "var(--muted)", fontSize: "0.9rem" }}>
          Loading map coordinates...
        </div>
      )}
      {error && (
        <div
          style={{
            background: "var(--danger-soft)",
            border: "1px solid var(--danger)",
            color: "var(--danger)",
            padding: "10px 14px",
            borderRadius: "8px",
            fontSize: "0.88rem",
            marginBottom: "12px",
          }}
        >
          {error}
        </div>
      )}

      {!loading && !error && (
        <div
          style={{
            position: "relative",
            width: "100%",
            height: "260px",
            backgroundColor: "#0e3d3f",
            borderRadius: "10px",
            overflow: "hidden",
            border: "1.5px solid var(--line)",
          }}
        >
          {/* SVG Map Container */}
          <svg width="100%" height="100%" viewBox="0 0 600 260" preserveAspectRatio="none">
            {/* Background grid */}
            <defs>
              <pattern id="mapGrid" width="24" height="24" patternUnits="userSpaceOnUse">
                <circle cx="2" cy="2" r="1" fill="#1b5e5a" opacity="0.6" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#mapGrid)" />

            <text
              x="300"
              y="135"
              textAnchor="middle"
              fill="#1b5e5a"
              fontSize="12"
              fontWeight="bold"
              letterSpacing="2"
            >
              KERALA DISTRICT COORDINATES · {district.toUpperCase()}
            </text>

            {/* Pins */}
            {features.map((f, i) => {
              const pt = projectCoords(f.geometry.coordinates);
              const isUrgent = f.properties.is_urgent;
              const isSelected = selectedFeature?.properties?.report_id === f.properties.report_id;

              return (
                <g
                  key={f.properties.report_id || i}
                  transform={`translate(${pt.x}, ${pt.y})`}
                  style={{ cursor: "pointer" }}
                  onClick={() => setSelectedFeature(f)}
                >
                  <circle
                    r={isSelected ? "11" : "8"}
                    fill={isUrgent ? "var(--danger)" : "var(--gold)"}
                    stroke="#ffffff"
                    strokeWidth="2.5"
                  />
                  <circle r="3.5" fill="#ffffff" />
                </g>
              );
            })}
          </svg>

          {features.length === 0 && (
            <div
              style={{
                position: "absolute",
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)",
                fontSize: "0.88rem",
                color: "#a5c2bc",
              }}
            >
              No consented coordinates available for {district}.
            </div>
          )}
        </div>
      )}

      {/* Selected Pin Quick Details (Panchayat removed) */}
      {selectedFeature && (
        <div
          style={{
            marginTop: "14px",
            backgroundColor: "#f7faf9",
            border: "1px solid var(--line)",
            borderRadius: "8px",
            padding: "12px 16px",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "10px",
          }}
        >
          <div>
            <strong style={{ fontSize: "0.95rem", color: "var(--teal-900)" }}>
              Case: {selectedFeature.properties.report_id}
            </strong>
            <span style={{ marginLeft: "12px", fontSize: "0.85rem", color: "var(--muted)" }}>
              Status: <strong>{selectedFeature.properties.status}</strong>
            </span>
            {selectedFeature.properties.is_urgent && (
              <span
                style={{
                  marginLeft: "10px",
                  fontSize: "0.75rem",
                  fontWeight: "700",
                  background: "var(--danger)",
                  color: "#ffffff",
                  padding: "2px 8px",
                  borderRadius: "12px",
                }}
              >
                Urgent
              </span>
            )}
          </div>
          <button
            type="button"
            className="btn btn-primary"
            style={{ minHeight: "36px", padding: "6px 14px", fontSize: "0.85rem", width: "auto" }}
            onClick={() => navigate(`/case/${selectedFeature.properties.report_id}`)}
          >
            Open Case Detail
          </button>
        </div>
      )}
    </div>
  );
}
