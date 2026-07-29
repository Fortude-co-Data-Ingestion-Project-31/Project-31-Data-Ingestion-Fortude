import React from "react";
import { COLORS, FONTS } from "../theme";

export default function Toast({ message }) {
  return (
    <div
      className="fixed left-1/2 bottom-6 -translate-x-1/2 px-5 py-3 rounded-md text-sm transition-all duration-300 z-50"
      style={{
        fontFamily: FONTS.mono,
        background: COLORS.panel,
        border: `1px solid ${COLORS.panelLine}`,
        color: COLORS.paper,
        opacity: message ? 1 : 0,
        transform: message ? "translate(-50%, 0)" : "translate(-50%, 20px)",
        pointerEvents: "none",
      }}
    >
      {message}
    </div>
  );
}
