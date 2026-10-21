import React, { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useT } from "../i18n";
import Hero from "../components/Hero";
import DemoNotice from "../components/DemoNotice";
import LanguageToggle from "../components/LanguageToggle";

const FALLBACK_DISTRICTS = [
  "Thiruvananthapuram", "Kollam", "Pathanamthitta", "Alappuzha", "Kottayam",
  "Idukki", "Ernakulam", "Thrissur", "Palakkad", "Malappuram",
  "Kozhikode", "Wayanad", "Kannur", "Kasaragod"
];

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

export default function Emergency() {
  const { t } = useT();
  const navigate = useNavigate();

  // States: 'idle' | 'connecting' | 'connected' | 'ended'
  const [callState, setCallState] = useState("idle");
  const [seconds, setSeconds] = useState(0);
  const [finalDuration, setFinalDuration] = useState("00:00");
  const [districts, setDistricts] = useState(FALLBACK_DISTRICTS);
  const [selectedDistrict, setSelectedDistrict] = useState(() => {
    return localStorage.getItem("emergency_district") || "Thiruvananthapuram";
  });
  const [shareLocation, setShareLocation] = useState(false);
  const [coords, setCoords] = useState(null);
  const [callId, setCallId] = useState(null);
  const [nonBlockingError, setNonBlockingError] = useState(null);

  const timerRef = useRef(null);

  // Load backend districts
  useEffect(() => {
    let isMounted = true;
    api.get("/api/locations/districts")
      .then((data) => {
        if (isMounted && Array.isArray(data) && data.length > 0) {
          setDistricts(data.map((d) => d.name));
        }
      })
      .catch((err) => {
        console.warn("Using fallback districts for emergency helpline:", err);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  // Handle location consent
  const handleLocationChange = (e) => {
    const checked = e.target.checked;
    setShareLocation(checked);
    if (checked && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = pos.coords.latitude;
          const lng = pos.coords.longitude;
          if (lat >= 8.0 && lat <= 13.0 && lng >= 74.5 && lng <= 77.8) {
            setCoords({ lat: Number(lat.toFixed(2)), lng: Number(lng.toFixed(2)) });
          } else {
            setCoords(null);
          }
        },
        () => {
          setCoords(null);
        },
        { timeout: 5000 }
      );
    } else {
      setCoords(null);
    }
  };

  const handleDistrictChange = (e) => {
    const dist = e.target.value;
    setSelectedDistrict(dist);
    try {
      localStorage.setItem("emergency_district", dist);
    } catch {}
  };

  // Start Call Handler
  const handleStartCall = async () => {
    setCallState("connecting");
    setSeconds(0);
    setNonBlockingError(null);

    // 1. Record emergency event in backend API
    try {
      const payload = {
        district: selectedDistrict,
        category: "Women Helpline (Demo)",
        description: "Simulated emergency helpline call initiated from web prototype",
      };
      if (coords && shareLocation) {
        payload.description += ` | Reporter approx location: ${coords.lat}, ${coords.lng}`;
      }

      const res = await api.post("/api/emergency", payload);
      if (res && res.call && res.call.id) {
        setCallId(res.call.id);
      }
    } catch (err) {
      console.warn("Emergency event logging note:", err.message);
      setNonBlockingError("Call logged in offline demo mode.");
    }

    // 2. Transition from Connecting to Connected after ~2 seconds
    setTimeout(() => {
      setCallState("connected");
    }, 2000);
  };

  // Running Timer effect for Connected state
  useEffect(() => {
    if (callState === "connected") {
      timerRef.current = setInterval(() => {
        setSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [callState]);

  // End Call Handler
  const handleEndCall = async () => {
    const durationStr = formatTime(seconds);
    setFinalDuration(durationStr);
    setCallState("ended");

    if (callId) {
      try {
        await api.patch(`/api/emergency/${callId}`, {
          status: "Resolved",
          notes: `Simulated helpline call ended. Duration: ${durationStr}`,
        });
      } catch (err) {
        // Non-blocking as per prompt specifications
        console.warn("Note on updating emergency call ended state:", err.message);
      }
    }
  };

  return (
    <div className="public-container">
      {/* Header with Back and Language toggle */}
      <div className="public-header">
        <div className="public-header-left">
          <Link to="/" className="back-link">
            {t("back")}
          </Link>
        </div>
        <LanguageToggle />
      </div>

      {/* Demo notice visible in all 4 states */}
      <DemoNotice variant="call" />

      {nonBlockingError && (
        <div
          style={{
            fontSize: "0.8rem",
            color: "var(--muted)",
            marginBottom: "10px",
            textAlign: "center",
          }}
        >
          {nonBlockingError}
        </div>
      )}

      {/* State 1: Idle */}
      {callState === "idle" && (
        <div>
          <Hero
            label={t("brand_tagline")}
            title={t("emergency_title")}
            subtitle={t("emergency_subtitle")}
          />

          <div className="content-card" style={{ textAlign: "center" }}>
            <div className="form-group" style={{ textAlign: "left", marginBottom: "16px" }}>
              <label htmlFor="emergency-district" className="form-label">
                {t("emergency_district_label")}
              </label>
              <select
                id="emergency-district"
                className="form-control"
                value={selectedDistrict}
                onChange={handleDistrictChange}
              >
                {districts.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group" style={{ textAlign: "left", marginBottom: "20px" }}>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={shareLocation}
                  onChange={handleLocationChange}
                />
                <span>{t("share_location")}</span>
              </label>
            </div>

            <button
              type="button"
              className="btn btn-danger"
              style={{ minHeight: "56px", fontSize: "1.15rem", marginBottom: "16px" }}
              onClick={handleStartCall}
            >
              <svg
                width="22"
                height="22"
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
              {t("start_call")}
            </button>

            <p style={{ fontSize: "0.85rem", color: "var(--muted)", lineHeight: "1.45" }}>
              {t("emergency_privacy_note")}
            </p>

            <div className="dialer-link-container">
              <a href="tel:112" className="dialer-link">
                {t("use_phone_dialer")}
              </a>
              <div className="dialer-caption">
                112 · {t("opens_phone_dialer")}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* State 2: Connecting */}
      {callState === "connecting" && (
        <div className="emergency-call-card">
          <div className="emergency-pulse-wrapper">
            <div className="pulse-ring" />
            <div className="pulse-ring pulse-ring-delayed" />
            <div className="emergency-phone-icon">
              <svg
                width="28"
                height="28"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
              </svg>
            </div>
          </div>

          <h2 className="emergency-helpline-name">{t("women_helpline")}</h2>
          <p className="emergency-status-text">{t("connecting_message")}</p>

          <div className="call-timer">00:00</div>

          <button
            type="button"
            className="end-call-btn"
            onClick={handleEndCall}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
            {t("end_call")}
          </button>
        </div>
      )}

      {/* State 3: Connected (demo) */}
      {callState === "connected" && (
        <div className="emergency-call-card">
          <div className="emergency-pulse-wrapper">
            <div className="emergency-phone-icon" style={{ background: "#25d366", color: "#ffffff" }}>
              <svg
                width="28"
                height="28"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
              </svg>
            </div>
          </div>

          <h2 className="emergency-helpline-name">{t("women_helpline")}</h2>
          <p className="emergency-status-text" style={{ color: "var(--gold)", fontWeight: "700" }}>
            {t("connected_demo")}
          </p>

          <div className="call-timer">{formatTime(seconds)}</div>

          <div className="gold-tip">
            {t("connected_tip")}
          </div>

          <button
            type="button"
            className="end-call-btn"
            onClick={handleEndCall}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
            {t("end_call")}
          </button>
        </div>
      )}

      {/* State 4: Ended */}
      {callState === "ended" && (
        <div className="content-card" style={{ textAlign: "center", padding: "36px 24px" }}>
          <div
            style={{
              width: "72px",
              height: "72px",
              borderRadius: "50%",
              background: "#eef7f4",
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              marginBottom: "16px",
            }}
          >
            <svg
              width="40"
              height="40"
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

          <h2 style={{ fontSize: "1.45rem", fontWeight: "800", color: "var(--teal-900)", marginBottom: "6px" }}>
            {t("call_ended")}
          </h2>
          <p style={{ fontFamily: "var(--font-mono)", fontSize: "1.1rem", color: "var(--muted)", marginBottom: "28px" }}>
            {t("call_duration")} {finalDuration}
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <Link to="/" className="btn btn-primary">
              {t("write_report_now")}
            </Link>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setCallState("idle");
                setSeconds(0);
                navigate("/");
              }}
            >
              {t("back_to_home")}
            </button>
          </div>
        </div>
      )}

      {/* Persistent footer */}
      <footer className="public-page-footer">
        {t("proto_footer")}
      </footer>
    </div>
  );
}
