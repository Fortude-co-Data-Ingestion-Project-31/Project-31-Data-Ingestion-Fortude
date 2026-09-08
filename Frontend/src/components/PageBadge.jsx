import React from "react";
import { COLORS } from "../theme";

export default function PageBadge({ label }) {
  return (
    <div className="px-8 pt-5 pb-3 text-lg" style={{ color: "#c7ccd3", fontWeight: 500 }}>
      {label}
    </div>
  );
}
