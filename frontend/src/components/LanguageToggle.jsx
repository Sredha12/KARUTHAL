import React from "react";
import { useT } from "../i18n";

export default function LanguageToggle() {
  const { lang, setLang } = useT();

  return (
    <div className="lang-pill-toggle" role="group" aria-label="Language selection">
      <button
        type="button"
        className={`lang-btn ${lang === "en" ? "active" : ""}`}
        onClick={() => setLang("en")}
        aria-pressed={lang === "en"}
      >
        English
      </button>
      <button
        type="button"
        className={`lang-btn ${lang === "ml" ? "active" : ""}`}
        onClick={() => setLang("ml")}
        aria-pressed={lang === "ml"}
      >
        മലയാളം
      </button>
    </div>
  );
}
