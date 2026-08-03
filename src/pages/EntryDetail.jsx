import React from "react";
import { ArrowLeft } from "lucide-react";
import { COLORS } from "../theme";
import PageHeading from "../components/PageHeading";

export default function EntryDetail({ entry, goTo }) {
  if (!entry) return null;

  const fields = [
    ["Connector", entry.connector],
    ["Mapper", entry.mapper || "<Mapper>"],
    ["Rules", entry.rules],
  ];

  return (
    <section>
      <div onClick={() => goTo("history")} className="inline-flex items-center gap-1.5 text-sm cursor-pointer mb-5 font-medium" style={{ color: COLORS.textMuted }}>
        <ArrowLeft size={14} /> Back to history
      </div>

      <PageHeading title={`Data Ingestion Entry ${entry.id}`} subtitle="What this run was built from, and where it sent the data." />

      <div className="rounded-lg p-8" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-7 mb-8">
          {fields.map(([label, value]) => (
            <div key={label}>
              <div className="text-xs font-semibold uppercase tracking-wide mb-1.5" style={{ color: COLORS.textFaint, letterSpacing: "0.05em" }}>
                {label}
              </div>
              <div className="font-semibold" style={{ color: COLORS.text, fontSize: 17 }}>{value}</div>
            </div>
          ))}
          <div>
            <div className="text-xs font-semibold uppercase tracking-wide mb-1.5" style={{ color: COLORS.textFaint, letterSpacing: "0.05em" }}>
              Run Status
            </div>
            <div className="font-semibold" style={{ color: "#15803d", fontSize: 15 }}>Completed</div>
          </div>
        </div>

        <div className="text-xs font-semibold uppercase tracking-wide mb-3" style={{ color: COLORS.textFaint, letterSpacing: "0.05em" }}>
          Outputs
        </div>
        <div className="flex flex-wrap gap-2.5">
          {entry.outputs.map((o) => (
            <div key={o} className="text-sm px-4 py-2 rounded-full font-medium" style={{ background: COLORS.badgeBg, border: `1px solid ${COLORS.border}`, color: COLORS.text }}>
              {o}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
