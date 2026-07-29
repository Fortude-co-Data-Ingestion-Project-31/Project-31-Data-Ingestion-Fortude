import React from "react";
import { Trash2 } from "lucide-react";
import { COLORS, FONTS } from "../theme";
import Dot from "./Dot";

export default function Row({ label, sub, onView, onDelete }) {
  return (
    <div className="flex items-center justify-between px-5 py-3 text-sm" style={{ borderBottom: `1px solid ${COLORS.inkSoft}` }}>
      <div className="flex items-center gap-2.5">
        <Dot />
        <span>{label}</span>
        {sub && <span className="text-xs ml-1" style={{ fontFamily: FONTS.mono, color: COLORS.slate }}>{sub}</span>}
      </div>
      <div className="flex items-center gap-3.5">
        {onView && (
          <button onClick={onView} className="text-xs bg-transparent border-none cursor-pointer" style={{ fontFamily: FONTS.mono, color: COLORS.steel }}>
            View
          </button>
        )}
        {onDelete && (
          <button onClick={onDelete} className="text-xs bg-transparent border-none cursor-pointer flex items-center gap-1" style={{ fontFamily: FONTS.mono, color: COLORS.bad }}>
            <Trash2 size={12} /> Delete
          </button>
        )}
      </div>
    </div>
  );
}
