import React from "react";
import { COLORS, FONTS } from "../theme";

export default function NavLink({ label, active, onClick }) {
  return (
    <div
      onClick={onClick}
      className="px-4 py-2 rounded cursor-pointer uppercase text-xs tracking-widest transition-all"
      style={{
        fontFamily: FONTS.mono,
        letterSpacing: "0.06em",
        color: active ? COLORS.signal : COLORS.slate,
        background: active ? "rgba(232,163,61,0.08)" : "transparent",
        border: `1px solid ${active ? "rgba(232,163,61,0.35)" : "transparent"}`,
      }}
    >
      {label}
    </div>
  );
}
