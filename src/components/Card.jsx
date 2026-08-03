import React from "react";
import { COLORS } from "../theme";

export default function Card({ title, count, children, footer, onFooterClick }) {
  return (
    <div className="rounded-lg overflow-hidden" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}>
      <div className="flex items-center justify-between px-6 py-4" style={{ borderBottom: `1px solid ${COLORS.borderSoft}` }}>
        <h3 className="m-0 font-semibold text-base" style={{ color: COLORS.text }}>{title}</h3>
        {count !== undefined && (
          <span
            className="flex items-center justify-center rounded-full text-xs font-semibold"
            style={{ width: 24, height: 24, background: COLORS.badgeBg, color: COLORS.badgeText, border: `1px solid ${COLORS.border}` }}
          >
            {count}
          </span>
        )}
      </div>
      <div className="flex flex-col">{children}</div>
      {footer && (
        <div
          onClick={onFooterClick}
          className="text-center py-4 text-sm cursor-pointer font-semibold"
          style={{ color: COLORS.orange, borderTop: `1px solid ${COLORS.borderSoft}` }}
        >
          {footer}
        </div>
      )}
    </div>
  );
}
