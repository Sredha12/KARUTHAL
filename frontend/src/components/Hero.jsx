import React from "react";

export default function Hero({ label, title, subtitle, note }) {
  return (
    <div className="hero-card">
      {label && <span className="hero-label">{label}</span>}
      <h1 className="hero-title">{title}</h1>
      {subtitle && <p className="hero-subtitle">{subtitle}</p>}
      {note && <p className="hero-note">{note}</p>}
    </div>
  );
}
