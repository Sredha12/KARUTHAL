import React from "react";
import { useT } from "../i18n";

export default function DemoNotice({ variant = "report", customText = null }) {
  const { t } = useT();

  let defaultText = t("report_notice");
  if (variant === "call" || variant === "emergency") {
    defaultText = t("emergency_notice");
  }

  const textToDisplay = customText || defaultText;

  return (
    <div className="demo-notice" role="alert">
      <span className="demo-notice-icon" aria-hidden="true">⚠️</span>
      <div>{textToDisplay}</div>
    </div>
  );
}
