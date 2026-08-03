import React from "react";
import { LayoutGrid, Activity, History as HistoryIcon, Settings, ChevronDown, X } from "lucide-react";
import { COLORS } from "../theme";

// The list of page links shown in the left navigation area.
const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard", icon: LayoutGrid },
  { key: "ingest", label: "Ingest", icon: Activity },
  { key: "history", label: "History", icon: HistoryIcon },
  { key: "configure", label: "Configuration", icon: Settings },
];

// Sidebar renders the main navigation and the user profile section on the left side of the app.
export default function Sidebar({ page, goTo, onClose = () => {} }) {
  return (
    <div
      className="flex flex-col justify-between flex-shrink-0"
      style={{ width: 220, background: COLORS.sidebar, borderRight: `1px solid ${COLORS.border}`, minHeight: "100vh" }}
    >
      <div>
        <div className="flex items-center justify-between gap-2.5 px-6 py-6">
          <div className="flex items-center gap-2.5">
            <div
              className="flex items-center justify-center rounded-md font-bold text-white flex-shrink-0"
              style={{ width: 30, height: 30, background: "linear-gradient(135deg, #2563eb, #0891b2)", fontFamily: "inherit" }}
            >
              F
            </div>
            <div className="text-sm font-semibold leading-tight" style={{ color: COLORS.text }}>
              Data Ingestion<br />Engine
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1.5 transition-colors hover:bg-slate-100"
            aria-label="Close sidebar navigation"
          >
            <X size={16} style={{ color: COLORS.textMuted }} />
          </button>
        </div>

        <nav className="mt-2 px-3" aria-label="Sidebar navigation">
          {NAV_ITEMS.map(({ key, label, icon: Icon }) => {
            const active = page === key;
            return (
              <div
                key={key}
                onClick={() => goTo(key)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-md cursor-pointer text-sm mb-1"
                style={{
                  background: active ? COLORS.blueSoft : "transparent",
                  color: active ? COLORS.blue : COLORS.textMuted,
                  fontWeight: active ? 600 : 500,
                }}
              >
                <Icon size={17} strokeWidth={2} />
                {label}
              </div>
            );
          })}
        </nav>
      </div>

      <div className="px-4 py-4" style={{ borderTop: `1px solid ${COLORS.border}` }}>
        <div className="flex items-center gap-2.5 cursor-pointer">
          <div
            className="flex items-center justify-center rounded-full text-white text-xs font-semibold flex-shrink-0"
            style={{ width: 32, height: 32, background: COLORS.blue }}
          >
            AS
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-semibold truncate" style={{ color: COLORS.text }}>Amanda Smith</div>
            <div className="text-xs truncate" style={{ color: COLORS.textFaint }}>amandasmith@gmail.com</div>
          </div>
          <ChevronDown size={15} style={{ color: COLORS.textFaint }} />
        </div>
      </div>
    </div>
  );
}
