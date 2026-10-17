import React, { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useT } from "../i18n";
import Hero from "../components/Hero";
import DemoNotice from "../components/DemoNotice";
import LanguageToggle from "../components/LanguageToggle";

const CATEGORY_ITEMS = [
  { value: "Physical abuse", key: "cat_physical" },
  { value: "Sexual abuse", key: "cat_sexual" },
  { value: "Emotional abuse", key: "cat_emotional" },
  { value: "Neglect", key: "cat_neglect" },
  { value: "Child labour", key: "cat_labour" },
  { value: "Child marriage", key: "cat_marriage" },
  { value: "Trafficking", key: "cat_trafficking" },
  { value: "Missing child", key: "cat_missing" },
  { value: "Other", key: "cat_other" },
];

export default function PublicReport() {
  const { t, lang } = useT();

  // Form states
  const [districts, setDistricts] = useState([]);
  const [category, setCategory] = useState(CATEGORY_ITEMS[0].value);
  const [description, setDescription] = useState("");
  const [locationText, setLocationText] = useState("");
  const [district, setDistrict] = useState("");
  const [approxTime, setApproxTime] = useState("");

  // Photo states
  const [photoPreview, setPhotoPreview] = useState(null);
  const [photoConfirmed, setPhotoConfirmed] = useState(false);

  // Immediate danger state: null | 'Yes' | 'No' | 'Not sure'
  const [immediateDanger, setImmediateDanger] = useState(null);

  // Approximate area consent & coords
  const [shareLocation, setShareLocation] = useState(false);
  const [coords, setCoords] = useState(null);
  const [locationStatus, setLocationStatus] = useState("");

  // Voice speech-to-text states
  const [voiceLang, setVoiceLang] = useState("ml-IN");
  const [isListening, setIsListening] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const recognitionRef = useRef(null);

  // Form submission & confirmation states
  const [submitting, setSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successData, setSuccessData] = useState(null);
  const [copiedToken, setCopiedToken] = useState(false);

  // Callback action states
  const [callbackLoading, setCallbackLoading] = useState(false);
  const [callbackRequested, setCallbackRequested] = useState(false);
  const [callbackNotice, setCallbackNotice] = useState("");
  const [callbackError, setCallbackError] = useState("");

  // Hidden file input refs
  const cameraInputRef = useRef(null);
  const galleryInputRef = useRef(null);

  // Check speech recognition support
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
    }
  }, []);

  // Fetch districts from backend
  useEffect(() => {
    api.get("/api/locations/districts")
      .then((data) => {
        if (Array.isArray(data)) {
          setDistricts(data);
          if (data.length > 0) {
            setDistrict(data[0].name);
          }
        }
      })
      .catch((err) => {
        console.warn("Could not load backend districts:", err.message);
      });
  }, []);

  // Handle Voice Recording toggle
  const toggleListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }

    if (isListening) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = voiceLang;
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event) => {
        if (event.results && event.results[0] && event.results[0][0]) {
          const transcript = event.results[0][0].transcript;
          setDescription((prev) => (prev ? `${prev} ${transcript}` : transcript));
        }
      };

      recognition.onerror = (event) => {
        console.warn("Speech recognition error:", event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.warn("Speech recognition start failed:", err);
      setIsListening(false);
    }
  };

  // Handle Photo selection
  const handlePhotoSelect = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (photoPreview) {
        URL.revokeObjectURL(photoPreview);
      }
      const previewUrl = URL.createObjectURL(file);
      setPhotoPreview(previewUrl);
      setPhotoConfirmed(false);
    }
  };

  const handleRemovePhoto = () => {
    if (photoPreview) {
      URL.revokeObjectURL(photoPreview);
    }
    setPhotoPreview(null);
    setPhotoConfirmed(false);
    if (cameraInputRef.current) cameraInputRef.current.value = "";
    if (galleryInputRef.current) galleryInputRef.current.value = "";
  };

  // Handle Location Consent toggle
  const handleLocationConsentChange = (e) => {
    const checked = e.target.checked;
    setShareLocation(checked);
    setLocationStatus("");

    if (checked) {
      if (!navigator.geolocation) {
        setLocationStatus(t("location_denied"));
        return;
      }
      setLocationStatus(t("location_locating"));
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = pos.coords.latitude;
          const lng = pos.coords.longitude;
          // Validate Kerala bounds: lat 8.0 - 12.8, lng 74.8 - 77.6
          if (lat >= 8.0 && lat <= 12.8 && lng >= 74.8 && lng <= 77.6) {
            setCoords({
              lat: Number(lat.toFixed(2)),
              lng: Number(lng.toFixed(2)),
            });
            setLocationStatus(t("location_active"));
          } else {
            setCoords(null);
            setLocationStatus(t("location_out_of_bounds"));
          }
        },
        () => {
          setCoords(null);
          setLocationStatus(t("location_denied"));
        },
        { timeout: 7000 }
      );
    } else {
      setCoords(null);
      setLocationStatus("");
    }
  };

  // Handle Form Submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage("");

    // Validate Description
    if (!description.trim() || description.trim().length < 10) {
      setErrorMessage(
        lang === "ml"
          ? "ദയവായി നിങ്ങൾ കണ്ട കാര്യങ്ങൾ വിശദമായി എഴുതുക (കുറഞ്ഞത് 10 അക്ഷരങ്ങൾ)."
          : "Please describe what you observed (at least 10 characters)."
      );
      return;
    }

    // Validate District
    if (!district) {
      setErrorMessage(
        lang === "ml" ? "ദയവായി ജില്ല തിരഞ്ഞെടുക്കുക." : "Please select a district."
      );
      return;
    }

    // Validate Immediate Danger
    if (!immediateDanger) {
      setErrorMessage(
        lang === "ml"
          ? "കുട്ടി അടിയന്തിര അപകടത്തിലാണോ എന്ന് തിരഞ്ഞെടുക്കുക (അതെ / അല്ല / ഉറപ്പില്ല)."
          : "Please indicate whether the child is in immediate danger (Yes / No / Not sure)."
      );
      return;
    }

    // Validate Photo confirmation if photo attached
    if (photoPreview && !photoConfirmed) {
      setErrorMessage(
        lang === "ml"
          ? "ഫോട്ടോയിൽ കുട്ടി ഇല്ലെന്ന് സ്ഥിരീകരിക്കുക."
          : "Please confirm that the photo does not show a child before submitting."
      );
      return;
    }

    // Build description narrative with approximate time and danger answer
    let finalDescription = description.trim();
    if (approxTime.trim()) {
      finalDescription += `\n\nApproximate time: ${approxTime.trim()}`;
    }
    finalDescription += `\n\nReporter's answer to immediate danger: ${immediateDanger}`;

    const isUrgent = immediateDanger === "Yes";

    const payload = {
      district: district,
      category: category,
      description: finalDescription,
      is_urgent: isUrgent,
      location_text: locationText.trim().slice(0, 200) || null,
      location_consent: shareLocation && coords !== null,
      approx_lat: shareLocation && coords ? coords.lat : null,
      approx_lng: shareLocation && coords ? coords.lng : null,
      location_source: shareLocation && coords ? "device" : "typed",
    };

    setSubmitting(true);
    try {
      const res = await api.post("/api/reports", payload);
      setSuccessData(res);
      // Persist reporter token in sessionStorage only
      if (res.reporter_token) {
        try {
          sessionStorage.setItem("karuthal_reporter_token", res.reporter_token);
          sessionStorage.setItem(`token_${res.report?.case_id || res.report?.report_id}`, res.reporter_token);
        } catch {}
      }
    } catch (err) {
      setErrorMessage(err.message || "Failed to submit report. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  // Copy Reporter Token
  const handleCopyToken = () => {
    if (successData?.reporter_token) {
      navigator.clipboard.writeText(successData.reporter_token);
      setCopiedToken(true);
      setTimeout(() => setCopiedToken(false), 3000);
    }
  };

  // Request Callback Action
  const handleRequestCallback = async () => {
    const caseId = successData?.report?.case_id || successData?.report?.report_id;
    const token = successData?.reporter_token;
    if (!caseId || !token) return;

    setCallbackLoading(true);
    setCallbackError("");
    try {
      const res = await api.post(`/api/reports/${caseId}/callback-request`, null, {
        reporterToken: token,
      });
      setCallbackRequested(true);
      setCallbackNotice(res.notice || t("callback_requested"));
    } catch (err) {
      setCallbackError(err.message || "Could not request callback at this time.");
    } finally {
      setCallbackLoading(false);
    }
  };

  const handleResetForm = () => {
    setSuccessData(null);
    setDescription("");
    setLocationText("");
    setApproxTime("");
    handleRemovePhoto();
    setImmediateDanger(null);
    setShareLocation(false);
    setCoords(null);
    setErrorMessage("");
    setCallbackRequested(false);
    setCallbackNotice("");
  };

  return (
    <div className="public-container">
      {/* Top Header with Brand and Language toggle */}
      <div className="public-header">
        <div className="public-header-left">
          <Link to="/" className="brand-link">
            <span>🛡️</span>
            <span>{t("brand_name")}</span>
          </Link>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <LanguageToggle />
          <Link to="/login" className="officer-login-link">
            {t("officer_login")}
          </Link>
        </div>
      </div>

      {/* Prominent Red Emergency Help Button */}
      <Link
        to="/emergency"
        className="btn btn-danger"
        style={{
          marginBottom: "16px",
          fontWeight: "800",
          boxShadow: "0 2px 8px rgba(179,38,30,0.3)",
        }}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
        </svg>
        {t("emergency_help")}
      </Link>

      {/* SUCCESS CONFIRMATION VIEW */}
      {successData ? (
        <div className="content-card" style={{ borderTop: "4px solid var(--teal-700)" }}>
          <div style={{ textAlign: "center", marginBottom: "20px" }}>
            <div
              style={{
                width: "60px",
                height: "60px",
                borderRadius: "50%",
                background: "#eef7f4",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                marginBottom: "12px",
              }}
            >
              <svg
                width="34"
                height="34"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#1b5e5a"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <h2 style={{ fontSize: "1.4rem", fontWeight: "800", color: "var(--teal-900)" }}>
              {t("report_success_title")}
            </h2>
            <p style={{ fontSize: "0.9rem", color: "var(--muted)", marginTop: "4px" }}>
              {t("report_success_subtitle")}
            </p>
          </div>

          <div
            style={{
              background: "#f4f8f7",
              borderRadius: "10px",
              padding: "16px",
              marginBottom: "18px",
              border: "1px solid var(--line)",
            }}
          >
            <div style={{ fontSize: "0.8rem", color: "var(--muted)", fontWeight: "600" }}>
              {t("case_ref_label")}
            </div>
            <div
              style={{
                fontSize: "1.35rem",
                fontWeight: "800",
                color: "var(--teal-900)",
                letterSpacing: "0.04em",
                margin: "4px 0 12px",
              }}
            >
              {successData.report?.case_id || successData.report?.report_id}
            </div>

            {successData.reporter_token && (
              <div
                style={{
                  borderTop: "1px dashed var(--line)",
                  paddingTop: "12px",
                }}
              >
                <div style={{ fontSize: "0.82rem", color: "var(--muted)", fontWeight: "600" }}>
                  {t("reporter_token_label")}
                </div>
                <div
                  style={{
                    fontFamily: "var(--font-mono)",
                    fontSize: "0.95rem",
                    fontWeight: "700",
                    background: "#ffffff",
                    padding: "8px 10px",
                    borderRadius: "6px",
                    border: "1px solid var(--line)",
                    margin: "6px 0",
                    wordBreak: "break-all",
                  }}
                >
                  {successData.reporter_token}
                </div>
                <div style={{ color: "var(--danger)", fontSize: "0.78rem", fontWeight: "600", marginBottom: "8px" }}>
                  ⚠️ {t("reporter_token_warning")}
                </div>
                <button
                  type="button"
                  className="btn btn-secondary"
                  style={{ minHeight: "40px", fontSize: "0.88rem" }}
                  onClick={handleCopyToken}
                >
                  {copiedToken ? t("token_copied") : t("copy_token")}
                </button>
              </div>
            )}
          </div>

          {/* Callback Section */}
          <div
            style={{
              border: "1px solid var(--line)",
              borderRadius: "10px",
              padding: "16px",
              marginBottom: "20px",
              background: "#ffffff",
            }}
          >
            <h3 style={{ fontSize: "0.95rem", fontWeight: "700", color: "var(--teal-900)", marginBottom: "4px" }}>
              {t("callback_title")}
            </h3>
            <p style={{ fontSize: "0.82rem", color: "var(--muted)", marginBottom: "12px" }}>
              {t("callback_desc")}
            </p>

            {callbackNotice && (
              <div
                style={{
                  background: "var(--gold-soft)",
                  border: "1px solid var(--gold)",
                  color: "#5a4505",
                  padding: "10px 12px",
                  borderRadius: "8px",
                  fontSize: "0.85rem",
                  marginBottom: "10px",
                }}
              >
                {callbackNotice}
              </div>
            )}

            {callbackError && (
              <div
                style={{
                  background: "var(--danger-soft)",
                  color: "var(--danger)",
                  padding: "10px 12px",
                  borderRadius: "8px",
                  fontSize: "0.85rem",
                  marginBottom: "10px",
                }}
              >
                {callbackError}
              </div>
            )}

            {!callbackRequested ? (
              <button
                type="button"
                className="btn btn-secondary"
                disabled={callbackLoading}
                onClick={handleRequestCallback}
              >
                {callbackLoading ? "Requesting..." : t("callback_btn")}
              </button>
            ) : (
              <div style={{ fontSize: "0.85rem", color: "var(--teal-700)", fontWeight: "600" }}>
                ✓ {t("callback_already_requested")}
              </div>
            )}
          </div>

          <button
            type="button"
            className="btn btn-primary"
            onClick={handleResetForm}
          >
            {t("submit_another")}
          </button>
        </div>
      ) : (
        /* REPORT SUBMISSION FORM */
        <div>
          <Hero
            label={t("brand_tagline")}
            title={t("report_title")}
            subtitle={t("report_subtitle")}
          />

          <DemoNotice variant="report" />

          {errorMessage && (
            <div
              style={{
                backgroundColor: "var(--danger-soft)",
                border: "1px solid var(--danger)",
                color: "var(--danger)",
                borderRadius: "10px",
                padding: "12px 14px",
                fontSize: "0.88rem",
                marginBottom: "16px",
              }}
              role="alert"
            >
              {errorMessage}
            </div>
          )}

          <form onSubmit={handleSubmit} className="content-card" noValidate>
            {/* Field 1: Type of concern */}
            <div className="form-group">
              <label htmlFor="concern-category" className="form-label form-label-required">
                {t("type_of_concern")}
              </label>
              <select
                id="concern-category"
                className="form-control"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                {CATEGORY_ITEMS.map((item) => (
                  <option key={item.value} value={item.value}>
                    {t(item.key)}
                  </option>
                ))}
              </select>
            </div>

            {/* Field 2: What did you see? */}
            <div className="form-group">
              <label htmlFor="concern-description" className="form-label form-label-required">
                {t("what_did_you_see")}
              </label>
              <div className="form-helper">{t("what_did_you_see_helper")}</div>
              <textarea
                id="concern-description"
                className="form-control"
                rows={4}
                placeholder={t("what_did_you_see_placeholder")}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
              />

              {/* Field 3: Voice box (dashed border) */}
              <div className="voice-box">
                <div className="voice-box-header">
                  <span style={{ fontSize: "0.84rem", fontWeight: "700", color: "var(--text)" }}>
                    🎙️ {t("voice_box_title")}
                  </span>
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <label htmlFor="voice-lang-select" style={{ fontSize: "0.8rem", color: "var(--muted)" }}>
                      {t("voice_lang")}:
                    </label>
                    <select
                      id="voice-lang-select"
                      className="voice-lang-select"
                      value={voiceLang}
                      onChange={(e) => setVoiceLang(e.target.value)}
                    >
                      <option value="ml-IN">മലയാളം (ml-IN)</option>
                      <option value="en-IN">English (en-IN)</option>
                    </select>
                  </div>
                </div>

                <button
                  type="button"
                  className={`voice-btn ${isListening ? "recording" : ""}`}
                  disabled={!speechSupported}
                  onClick={toggleListening}
                >
                  <span style={{ fontSize: "1.1rem" }}>
                    {isListening ? "🛑" : "🎤"}
                  </span>
                  <span>
                    {isListening
                      ? t("voice_listening")
                      : t("voice_speak")}
                  </span>
                </button>

                <div className="form-helper" style={{ marginTop: "8px", marginBottom: "0" }}>
                  {speechSupported ? t("voice_helper") : t("voice_unsupported")}
                </div>
              </div>
            </div>

            {/* Field 4: Where did you see it? */}
            <div className="form-group">
              <label htmlFor="concern-location" className="form-label">
                {t("where_did_you_see")}
              </label>
              <div className="form-helper">{t("where_helper")}</div>
              <input
                id="concern-location"
                type="text"
                className="form-control"
                maxLength={200}
                placeholder={t("where_placeholder")}
                value={locationText}
                onChange={(e) => setLocationText(e.target.value)}
              />
            </div>

            {/* Field 5: District (Required, populated from backend, NO panchayat) */}
            <div className="form-group">
              <label htmlFor="concern-district" className="form-label form-label-required">
                {t("district")}
              </label>
              <select
                id="concern-district"
                className="form-control"
                value={district}
                onChange={(e) => setDistrict(e.target.value)}
                required
              >
                {districts.map((d) => (
                  <option key={d.id || d.name} value={d.name}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Field 6: Approximate time */}
            <div className="form-group">
              <label htmlFor="concern-approx-time" className="form-label">
                {t("approx_time")}
              </label>
              <input
                id="concern-approx-time"
                type="text"
                className="form-control"
                placeholder={t("approx_time_placeholder")}
                value={approxTime}
                onChange={(e) => setApproxTime(e.target.value)}
              />
            </div>

            {/* Field 7: Photo (optional) */}
            <div className="photo-box">
              <label className="form-label">{t("photo_title")}</label>
              <div className="form-helper">{t("photo_helper")}</div>

              <div className="photo-warning">
                <span>⛔</span>
                <span>{t("photo_warning")}</span>
              </div>

              {/* Hidden file inputs */}
              <input
                type="file"
                accept="image/*"
                capture="environment"
                ref={cameraInputRef}
                style={{ display: "none" }}
                onChange={handlePhotoSelect}
              />
              <input
                type="file"
                accept="image/*"
                ref={galleryInputRef}
                style={{ display: "none" }}
                onChange={handlePhotoSelect}
              />

              {!photoPreview ? (
                <div className="photo-actions">
                  <button
                    type="button"
                    className="photo-btn"
                    onClick={() => cameraInputRef.current?.click()}
                  >
                    <span>📷</span>
                    <span>{t("photo_take")}</span>
                  </button>
                  <button
                    type="button"
                    className="photo-btn"
                    onClick={() => galleryInputRef.current?.click()}
                  >
                    <span>🖼️</span>
                    <span>{t("photo_choose")}</span>
                  </button>
                </div>
              ) : (
                <div>
                  <div className="photo-preview-wrap">
                    <img src={photoPreview} alt="Preview" className="photo-preview-img" />
                    <button
                      type="button"
                      className="photo-remove-btn"
                      onClick={handleRemovePhoto}
                    >
                      {t("photo_remove")}
                    </button>
                  </div>

                  <div className="form-group" style={{ marginBottom: "8px" }}>
                    <label className="checkbox-label" style={{ fontWeight: "600", color: "var(--teal-900)" }}>
                      <input
                        type="checkbox"
                        checked={photoConfirmed}
                        onChange={(e) => setPhotoConfirmed(e.target.checked)}
                        required
                      />
                      <span>{t("photo_confirm_no_child")}</span>
                    </label>
                  </div>
                </div>
              )}

              <div style={{ fontSize: "0.78rem", color: "var(--muted)", fontStyle: "italic" }}>
                {t("photo_not_uploaded_notice")}
              </div>
            </div>

            {/* Field 8: Is the child in immediate danger? (3 buttons, single choice, required) */}
            <div className="form-group">
              <label className="form-label form-label-required">
                {t("immediate_danger_title")}
              </label>
              <div className="segmented-group" role="radiogroup">
                <button
                  type="button"
                  className={`segmented-btn ${immediateDanger === "Yes" ? "selected-danger" : ""}`}
                  onClick={() => setImmediateDanger("Yes")}
                  aria-checked={immediateDanger === "Yes"}
                  role="radio"
                >
                  {t("immediate_danger_yes")}
                </button>
                <button
                  type="button"
                  className={`segmented-btn ${immediateDanger === "No" ? "selected" : ""}`}
                  onClick={() => setImmediateDanger("No")}
                  aria-checked={immediateDanger === "No"}
                  role="radio"
                >
                  {t("immediate_danger_no")}
                </button>
                <button
                  type="button"
                  className={`segmented-btn ${immediateDanger === "Not sure" ? "selected" : ""}`}
                  onClick={() => setImmediateDanger("Not sure")}
                  aria-checked={immediateDanger === "Not sure"}
                  role="radio"
                >
                  {t("immediate_danger_not_sure")}
                </button>
              </div>
            </div>

            {/* Field 9: Small optional checkbox for area sharing */}
            <div className="form-group" style={{ marginTop: "20px", marginBottom: "24px" }}>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={shareLocation}
                  onChange={handleLocationConsentChange}
                />
                <span>{t("share_location")}</span>
              </label>
              {locationStatus && (
                <div style={{ fontSize: "0.8rem", color: "var(--muted)", marginTop: "6px", marginLeft: "30px" }}>
                  {locationStatus}
                </div>
              )}
            </div>

            {/* Field 10: Primary Submit button */}
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? t("submitting") : t("submit_report")}
            </button>

            {/* Legal Footer Note */}
            <p className="legal-footer-note">
              {t("report_legal_footer")}
            </p>
          </form>
        </div>
      )}

      {/* Persistent Footer on every public screen */}
      <footer className="public-page-footer">
        {t("proto_footer")}
      </footer>
    </div>
  );
}
