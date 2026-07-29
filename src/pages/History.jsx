import React from "react";
import { Trash2 } from "lucide-react";
import { COLORS, FONTS } from "../theme";
import PageHeading from "../components/PageHeading";

export default function History({ history, openEntry, deleteEntry }) {
  return (
    <section>
      <PageHeading eyebrow="// audit trail" title="Data Ingestion History" subtitle="Every ingestion run, in the order it happened." />

      <div className="rounded-md overflow-hidden" style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelLine}` }}>
        <div
          className="hidden md:grid px-6 py-3.5 text-xs uppercase tracking-widest"
          style={{ gridTemplateColumns: "70px 1fr 180px 140px", fontFamily: FONTS.mono, letterSpacing: "0.08em", color: COLORS.slate, borderBottom: `1px solid ${COLORS.panelLine}` }}
        >
          <span>ID</span><span>Entry</span><span>Status</span><span></span>
        </div>
        {history.slice().reverse().map((e) => (
          <div
            key={e.id}
            className="grid grid-cols-1 md:grid px-6 py-4 items-center text-sm gap-1.5"
            style={{ gridTemplateColumns: "70px 1fr 180px 140px", borderBottom: `1px solid ${COLORS.inkSoft}` }}
          >
            <span style={{ fontFamily: FONTS.mono, color: COLORS.slate }}>#{String(e.id).padStart(3, "0")}</span>
            <span>
              Entry {e.id} <span className="text-xs ml-1" style={{ fontFamily: FONTS.mono, color: COLORS.slate }}>{e.connector}</span>
            </span>
            <span
              className="text-xs w-fit px-2.5 py-1 rounded-full"
              style={{ fontFamily: FONTS.mono, background: "rgba(95,172,127,0.15)", color: COLORS.good, border: "1px solid rgba(95,172,127,0.4)" }}
            >
              completed
            </span>
            <div className="flex gap-4 justify-start md:justify-end">
              <button onClick={() => openEntry(e.id)} className="text-xs bg-transparent border-none cursor-pointer" style={{ fontFamily: FONTS.mono, color: COLORS.steel }}>
                View
              </button>
              <button onClick={() => deleteEntry(e.id)} className="text-xs bg-transparent border-none cursor-pointer flex items-center gap-1" style={{ fontFamily: FONTS.mono, color: COLORS.bad }}>
                <Trash2 size={12} /> Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
