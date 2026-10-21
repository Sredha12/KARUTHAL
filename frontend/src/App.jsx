import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Link, useNavigate, useLocation } from "react-router-dom";
import PublicReport from "./pages/PublicReport";
import Emergency from "./pages/Emergency";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import CaseDetail from "./pages/CaseDetail";
import { getOfficerSession, clearOfficerSession } from "./api";

function OfficerHeader() {
  const [session, setSession] = useState(getOfficerSession());
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const check = () => setSession(getOfficerSession());
    window.addEventListener("storage", check);
    return () => window.removeEventListener("storage", check);
  }, []);

  // Only show the officer header on authenticated officer dashboard / case pages
  const isOfficerRoute = location.pathname.startsWith("/dashboard") || location.pathname.startsWith("/case");
  if (!isOfficerRoute) {
    return null;
  }

  const handleLogout = () => {
    clearOfficerSession();
    setSession(null);
    navigate("/login");
  };

  return (
    <header style={{ background: "var(--teal-900)", borderBottom: "3px solid var(--gold)", color: "#ffffff" }}>
      <div
        style={{
          background: "var(--teal-950)",
          color: "var(--gold)",
          fontSize: "0.78rem",
          padding: "6px 16px",
          textAlign: "center",
          letterSpacing: "0.04em",
          fontWeight: "600",
        }}
      >
        SIMULATED PROTOTYPE · Academic & Technical Evaluation Only. No real helpline or authority contacted.
      </div>
      <div
        style={{
          maxWidth: "1140px",
          margin: "0 auto",
          padding: "12px 20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <Link
            to="/dashboard"
            style={{
              color: "#ffffff",
              textDecoration: "none",
              fontWeight: "800",
              fontSize: "1.1rem",
              letterSpacing: "0.05em",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>🛡️</span>
            <span>KARUTHAL OFFICER</span>
          </Link>
          <Link
            to="/dashboard"
            style={{
              color: "#d1e2e0",
              textDecoration: "none",
              fontSize: "0.9rem",
              fontWeight: "600",
              padding: "4px 8px",
              borderRadius: "6px",
            }}
          >
            Dashboard
          </Link>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          {session && (
            <span
              style={{
                fontSize: "0.84rem",
                background: "rgba(201, 162, 39, 0.2)",
                color: "var(--gold)",
                border: "1px solid var(--gold)",
                padding: "4px 12px",
                borderRadius: "20px",
                fontWeight: "700",
              }}
            >
              {session.name} ({session.district})
            </span>
          )}
          <button
            type="button"
            onClick={handleLogout}
            style={{
              background: "transparent",
              border: "1px solid #3c716e",
              color: "#ffffff",
              padding: "6px 14px",
              borderRadius: "8px",
              fontSize: "0.85rem",
              fontWeight: "600",
              cursor: "pointer",
            }}
          >
            Sign Out
          </button>
        </div>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <Router>
      <div className="app-viewport">
        <OfficerHeader />
        <main style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          <Routes>
            <Route path="/" element={<PublicReport />} />
            <Route path="/emergency" element={<Emergency />} />
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/case/:id" element={<CaseDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
