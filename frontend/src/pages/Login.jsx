import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { api, setOfficerSession } from "../api";
import { useT } from "../i18n";
import LanguageToggle from "../components/LanguageToggle";

export default function Login() {
  const { t } = useT();
  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showForgotMsg, setShowForgotMsg] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();

  const isSessionExpired = new URLSearchParams(location.search).get("session_expired") === "1";

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    if (!loginId.trim() || !password) {
      setError(t("officer_id_or_email") + " & " + t("password") + " are required.");
      return;
    }

    setLoading(true);

    try {
      const data = await api.post("/api/login", {
        login: loginId.trim(),
        password,
      });

      setOfficerSession(data.token, data.name, data.district);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Invalid officer credentials or access restricted.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="officer-login-screen">
      <div className="officer-login-container">
        {/* Top Header with Back to Home & Language Toggle */}
        <div className="public-header" style={{ marginBottom: "12px" }}>
          <Link to="/" className="back-link" style={{ color: "#d1e2e0" }}>
            {t("back")}
          </Link>
          <LanguageToggle />
        </div>

        {/* Arch Hero Pattern */}
        <div className="officer-arch-hero">
          <svg
            width="80"
            height="80"
            viewBox="0 0 84 84"
            fill="none"
            className="officer-arch-svg"
            aria-hidden="true"
          >
            <path
              d="M14 74 V38 C14 22.5 26.5 10 42 10 C57.5 10 70 22.5 70 38 V74"
              stroke="var(--gold)"
              strokeWidth="3.2"
              strokeLinecap="round"
            />
            <path d="M10 74 H74" stroke="var(--gold)" strokeWidth="3.2" strokeLinecap="round" />
            <circle cx="42" cy="36" r="8.5" fill="var(--gold)" />
            <path
              d="M27 63 C27 52 33 47 42 47 C51 47 57 52 57 63"
              stroke="var(--gold)"
              strokeWidth="3.2"
              strokeLinecap="round"
              fill="none"
            />
          </svg>
          <h1 className="officer-brand-title">Karuthal</h1>
          <div className="officer-brand-subtitle">{t("care_before_crisis")}</div>
        </div>

        {/* Officer Login Form Card */}
        <div className="officer-login-card">
          <h2 style={{ fontSize: "1.25rem", fontWeight: "800", color: "#ffffff", marginBottom: "4px" }}>
            {t("officer_signin_title")}
          </h2>
          <p style={{ fontSize: "0.84rem", color: "#a5c2bc", marginBottom: "18px", lineHeight: "1.4" }}>
            {t("officer_signin_subtitle")}
          </p>

          {isSessionExpired && (
            <div
              style={{
                background: "rgba(201, 162, 39, 0.15)",
                border: "1px solid var(--gold)",
                color: "var(--gold)",
                padding: "10px 12px",
                borderRadius: "8px",
                fontSize: "0.84rem",
                marginBottom: "16px",
              }}
            >
              Your session has ended. Please sign in again.
            </div>
          )}

          {error && (
            <div
              style={{
                background: "rgba(179, 38, 30, 0.2)",
                border: "1px solid var(--danger)",
                color: "#ff8580",
                padding: "10px 12px",
                borderRadius: "8px",
                fontSize: "0.84rem",
                marginBottom: "16px",
              }}
              role="alert"
            >
              {error}
            </div>
          )}

          {showForgotMsg && (
            <div
              style={{
                background: "rgba(201, 162, 39, 0.15)",
                border: "1px solid var(--gold)",
                color: "#ffdd80",
                padding: "10px 12px",
                borderRadius: "8px",
                fontSize: "0.84rem",
                marginBottom: "16px",
              }}
            >
              {t("forgot_password_message")}
            </div>
          )}

          <form onSubmit={handleLogin} noValidate>
            <div className="form-group">
              <label htmlFor="officer-login-id" className="form-label">
                {t("officer_id_or_email")}
              </label>
              <input
                id="officer-login-id"
                type="text"
                className="form-control"
                placeholder={t("officer_id_placeholder")}
                value={loginId}
                onChange={(e) => setLoginId(e.target.value)}
                required
                autoFocus
              />
            </div>

            <div className="form-group" style={{ marginBottom: "6px" }}>
              <label htmlFor="officer-password" className="form-label">
                {t("password")}
              </label>
              <div className="input-password-wrap">
                <input
                  id="officer-password"
                  type={showPassword ? "text" : "password"}
                  className="form-control"
                  style={{ paddingRight: "60px" }}
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className="password-toggle-btn"
                  onClick={() => setShowPassword((prev) => !prev)}
                  aria-label={showPassword ? t("hide_password") : t("show_password")}
                >
                  {showPassword ? t("hide_password") : t("show_password")}
                </button>
              </div>
            </div>

            <div style={{ textAlign: "right", marginBottom: "16px" }}>
              <button
                type="button"
                className="forgot-password-link"
                onClick={() => setShowForgotMsg(true)}
              >
                {t("forgot_password")}
              </button>
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{
                background: "var(--teal-700)",
                color: "#ffffff",
                boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
              }}
              disabled={loading}
            >
              {loading ? t("signing_in") : t("sign_in")}
            </button>

            <p className="officer-login-notice">
              {t("officer_notice_line")}
            </p>
          </form>

          {/* Divider */}
          <div className="login-divider">
            {t("no_signin_needed_divider")}
          </div>

          {/* Quick Navigation Buttons */}
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <Link
              to="/"
              className="btn btn-secondary"
              style={{
                background: "#133f3e",
                borderColor: "#215553",
                color: "#ffffff",
              }}
            >
              {t("report_concern")}
            </Link>

            <Link
              to="/emergency"
              className="btn"
              style={{
                background: "rgba(179, 38, 30, 0.2)",
                border: "1.5px solid var(--danger)",
                color: "#ff9b96",
              }}
            >
              🚨 {t("emergency_help")}
            </Link>
          </div>
        </div>

        {/* Footer */}
        <footer className="public-page-footer" style={{ color: "#7a9c97" }}>
          {t("proto_footer")}
        </footer>
      </div>
    </div>
  );
}
