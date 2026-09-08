import React from "react";
import { COLORS } from "../theme";

export default function Row({ label, sub, onEdit, onDelete }) {
  return (
    <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: `1px solid ${COLORS.borderSoft}` }}>
      <div>
        <span className="text-sm" style={{ color: COLORS.text }}>{label}</span>
        {sub && <span className="text-xs ml-2" style={{ color: COLORS.textFaint }}>{sub}</span>}
      </div>
      <div className="flex items-center gap-5">
        {onEdit && (
          <button onClick={onEdit} className="text-sm bg-transparent border-none cursor-pointer font-medium" style={{ color: COLORS.blue }}>
            Edit
          </button>
        )}
        {onDelete && (
          <button onClick={onDelete} className="text-sm bg-transparent border-none cursor-pointer font-medium" style={{ color: COLORS.red }}>
            Delete
          </button>
        )}
      </div>
    </div>
  );
}
