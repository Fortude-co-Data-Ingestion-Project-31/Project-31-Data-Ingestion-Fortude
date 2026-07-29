import React from "react";
import { COLORS, FONTS } from "../theme";

export default function Select({ value, onChange, options, placeholder }) {
  return (
    <select
      value={value}
      onChange={onChange}
      className="w-full px-3.5 py-3 rounded text-sm cursor-pointer"
      style={{
        fontFamily: FONTS.mono,
        background: COLORS.inkSoft,
        border: `1px solid ${COLORS.panelLine}`,
        color: COLORS.paper,
        appearance: "none",
        WebkitAppearance: "none",
        backgroundImage:
          "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%238d97a8'/%3E%3C/svg%3E\")",
        backgroundRepeat: "no-repeat",
        backgroundPosition: "right 14px center",
      }}
    >
      <option value="">{placeholder}</option>
      {options.map((o) => (
        <option key={o} value={o}>{o}</option>
      ))}
    </select>
  );
}
