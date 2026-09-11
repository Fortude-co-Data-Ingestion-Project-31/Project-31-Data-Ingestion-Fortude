import React from "react";
import { COLORS } from "../theme";

export default function Toast({ message }) {
  return (
    <div
      className="fixed left-1/2 bottom-6 -translate-x-1/2 px-5 py-3 rounded-md text-sm transition-all duration-300 z-50"
      style={{
        background: COLORS.text,
        color: "#ffffff",
        opacity: message ? 1 : 0,
        transform: message ? "translate(-50%, 0)" : "translate(-50%, 20px)",
        pointerEvents: "none",
        boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
      }}
    >
      {message}
    </div>
  );
}
