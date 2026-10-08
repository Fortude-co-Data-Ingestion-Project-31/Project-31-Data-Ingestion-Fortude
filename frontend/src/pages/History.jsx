import React from "react";
import { COLORS } from "../theme";
import PageHeading from "../components/PageHeading";

export default function History({ history, openEntry, deleteEntry }) {
  return (
    <section>
      <PageHeading title="Data Ingestion History" subtitle="Every ingestion run, in the order it happened." />

      <div className="rounded-lg overflow-hidden" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}>
        <div
          className="hidden md:grid px-6 py-3.5 text-xs font-semibold uppercase tracking-wide"
          style={{ gridTemplateColumns: "70px 1fr 160px 140px", color: COLORS.textFaint, borderBottom: `1px solid ${COLORS.borderSoft}`, letterSpacing: "0.05em" }}
        >
          <span>ID</span><span>Entry</span><span>Status</span><span></span>
        </div>
        {history.slice().reverse().map((e) => (
          <div
            key={e.id}
            className="grid grid-cols-1 md:grid px-6 py-4 items-center text-sm gap-1.5"
            style={{ gridTemplateColumns: "70px 1fr 160px 140px", borderBottom: `1px solid ${COLORS.borderSoft}` }}
          >
            <span style={{ color: COLORS.textFaint }}>#{String(e.id).padStart(3, "0")}</span>
            <span style={{ color: COLORS.text }}>
              Entry {e.id} <span className="text-xs ml-1" style={{ color: COLORS.textFaint }}>{e.connector}</span>
            </span>
            <span
              className="text-xs w-fit px-2.5 py-1 rounded-full font-medium"
              style={{ background: "#ecfdf3", color: "#15803d", border: "1px solid #bbf7d0" }}
            >
              completed
            </span>
            <div className="flex gap-5 justify-start md:justify-end">
              <button onClick={() => openEntry(e.id)} className="text-sm bg-transparent border-none cursor-pointer font-medium" style={{ color: COLORS.blue }}>
                View
              </button>
              <button onClick={() => deleteEntry(e.id)} className="text-sm bg-transparent border-none cursor-pointer font-medium" style={{ color: COLORS.red }}>
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
