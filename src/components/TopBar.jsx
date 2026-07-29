import React from "react";
import { COLORS, FONTS } from "../theme";
import NavLink from "./NavLink";

export default function TopBar({ page, goTo }) {
  return (
    <div
      className="flex items-center justify-between px-8 py-4 sticky top-0 z-20"
      style={{ background: COLORS.inkSoft, borderBottom: `1px solid ${COLORS.panelLine}` }}
    >
      <div className="flex items-center gap-2.5 cursor-pointer select-none" onClick={() => goTo("dashboard")}>
        <div className="rounded-full" style={{ width: 11, height: 11, background: COLORS.signal, boxShadow: "0 0 0 3px rgba(232,163,61,0.15)" }} />
        <div className="font-bold text-lg tracking-wide" style={{ fontFamily: FONTS.display }}>
          FORTUDE <span style={{ color: COLORS.slate, fontWeight: 500 }}>/ ingestion</span>
        </div>
      </div>
      <div className="flex items-center">
        <div className="hidden md:flex items-center gap-1.5">
          <NavLink label="Ingest" active={page === "ingest"} onClick={() => goTo("ingest")} />
          <NavLink label="History" active={page === "history"} onClick={() => goTo("history")} />
          <NavLink label="Configure" active={page === "configure"} onClick={() => goTo("configure")} />
        </div>
        <div className="rounded-full ml-3.5" style={{ width: 30, height: 30, background: `linear-gradient(135deg, ${COLORS.steel}, ${COLORS.signal})` }} />
      </div>
    </div>
  );
}
