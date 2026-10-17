import React, { useState, useEffect } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const CATEGORIES = [
  "Physical abuse",
  "Sexual abuse",
  "Emotional abuse",
  "Neglect",
  "Child labour",
  "Child marriage",
  "Trafficking",
  "Abandonment",
  "Other",
];

export default function PublicReportForm() {
  const [districts, setDistricts] = useState([]);
  const [panchayats, setPanchayats] = useState([]);
  const [selectedDistrict, setSelectedDistrict] = useState("");
  const [selectedPanchayat, setSelectedPanchayat] = useState("");
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [description, setDescription] = useState("");
  const [isUrgent, setIsUrgent] = useState(false);

  const [loading, setLoading] = useState(false);
  const [panchayatLoading, setPanchayatLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [submittedCase, setSubmittedCase] = useState(null);

  // Load Kerala revenue districts on mount
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/locations/districts`)
      .then((res) => res.json())
      .then((data) => setDistricts(data))
      .catch(() => setErrorMessage("Failed to load Kerala districts."));
  }, []);

  // When district changes, clear selected panchayat and load child panchayats
  const handleDistrictChange = async (e) => {
    const distName = e.target.value;
    setSelectedDistrict(distName);
    setSelectedPanchayat("");
    setPanchayats([]);

    if (!distName) return;

    const distObj = districts.find((d) => d.name === distName);
    if (!distObj) return;

    setPanchayatLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/locations/panchayats?district_id=${distObj.id}`);
      const data = await res.json();
      setPanchayats(data);
    } catch (err) {
      setErrorMessage("Failed to load local administrative bodies.");
    } finally {
      setPanchayatLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage("");
    setSubmittedCase(null);

    if (description.trim().length < 10) {
      setErrorMessage("Description must be at least 10 characters long.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/reports`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          district: selectedDistrict,
          panchayat: selectedPanchayat,
          category,
          description: description.trim(),
          is_urgent: isUrgent,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.message || "Failed to submit report.");
      }

      setSubmittedCase(data.report);
      setDescription("");
      setIsUrgent(false);
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 640, margin: "20px auto", fontFamily: "system-ui, sans-serif" }}>
      <h2>Karuthal: Report a Child-Protection Concern</h2>
      <p style={{ color: "#666", fontSize: "0.9rem" }}>
        Privacy Guarantee: Submissions are confidential. Do not submit real identities, phone numbers,
        or personal addresses in public reports.
      </p>

      {errorMessage && (
        <div style={{ padding: 12, background: "#fee2e2", color: "#991b1b", borderRadius: 6, marginBottom: 16 }}>
          {errorMessage}
        </div>
      )}

      {submittedCase ? (
        <div style={{ padding: 16, background: "#ecfdf5", border: "1px solid #10b981", borderRadius: 8 }}>
          <h3 style={{ color: "#065f46", margin: "0 0 8px 0" }}>Report Submitted Successfully</h3>
          <p>
            Your tracking Case ID: <strong>{submittedCase.case_id}</strong>
          </p>
          <p style={{ fontSize: "0.85rem", color: "#047857" }}>
            Please store this reference to check your report status. No authority has been contacted automatically.
          </p>
          <button
            onClick={() => setSubmittedCase(null)}
            style={{ padding: "8px 16px", background: "#059669", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}
          >
            Submit Another Report
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>District *</label>
            <select
              value={selectedDistrict}
              onChange={handleDistrictChange}
              required
              style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
            >
              <option value="">-- Select Kerala District --</option>
              {districts.map((d) => (
                <option key={d.id} value={d.name}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>
              Panchayat / Local Administrative Unit *
            </label>
            <select
              value={selectedPanchayat}
              onChange={(e) => setSelectedPanchayat(e.target.value)}
              required
              disabled={!selectedDistrict || panchayatLoading}
              style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
            >
              <option value="">
                {panchayatLoading ? "Loading panchayats..." : selectedDistrict ? "-- Select Panchayat --" : "-- Select District First --"}
              </option>
              {panchayats.map((p) => (
                <option key={p.id} value={p.name}>
                  {p.name} (Sample)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>Concern Category *</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
            >
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontWeight: 600, marginBottom: 4 }}>
              Observations & Situation Details * (10-2000 chars)
            </label>
            <textarea
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              placeholder="Describe observations factually without personal names or private identifiers..."
              style={{ width: "100%", padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
            />
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              id="urgentCheck"
              checked={isUrgent}
              onChange={(e) => setIsUrgent(e.target.checked)}
            />
            <label htmlFor="urgentCheck" style={{ fontWeight: 600, color: "#dc2626" }}>
              Mark as Urgent (immediate child protection attention requested)
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              padding: "10px 18px",
              background: loading ? "#9ca3af" : "#2563eb",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Submitting Report..." : "Submit Anonymous Report"}
          </button>
        </form>
      )}
    </div>
  );
}
