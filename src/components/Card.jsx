import React from "react";
import { COLORS, FONTS } from "../theme";

export default function Card({ title, chip, children, footer, onFooterClick }) {
  return (
    <div className="rounded-md overflow-hidden" style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelLine}` }}>
      <div className="flex items-center justify-between px-5 py-4" style={{ borderBottom: `1px solid ${COLORS.panelLine}` }}>
        <h3 className="m-0 font-semibold text-base" style={{ fontFamily: FONTS.display }}>{title}</h3>
        {chip && (
          <span
            className="text-xs px-2.5 py-1 rounded-full"
            style={{ fontFamily: FONTS.mono, color: COLORS.slate, background: COLORS.inkSoft, border: `1px solid ${COLORS.panelLine}` }}
          >
            {chip}
          </span>
        )}
      </div>
      <div className="flex flex-col">{children}</div>
      {footer && (
        <div
          onClick={onFooterClick}
          className="text-center py-3 text-xs cursor-pointer tracking-wide"
          style={{ fontFamily: FONTS.mono, color: COLORS.slate, borderTop: `1px solid ${COLORS.panelLine}`, background: COLORS.inkSoft }}
        >
          {footer}
        </div>
      )}
    </div>
  );
}
