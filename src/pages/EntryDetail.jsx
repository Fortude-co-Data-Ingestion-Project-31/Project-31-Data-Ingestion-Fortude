import React from "react";
import { ArrowLeft } from "lucide-react";
import { COLORS, FONTS } from "../theme";
import Dot from "../components/Dot";
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
      <div onClick={() => goTo("history")} className="inline-flex items-center gap-1.5 text-xs cursor-pointer mb-6" style={{ fontFamily: FONTS.mono, color: COLORS.slate }}>
        <ArrowLeft size={13} /> Back to history
      </div>

      <PageHeading
        eyebrow="// run detail"
        title={`Data Ingestion Entry ${entry.id}`}
        subtitle="What this run was built from, and where it sent the data."
      />

      <div className="rounded-md p-10" style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelLine}` }}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          {fields.map(([label, value]) => (
            <div key={label}>
              <div className="text-xs uppercase tracking-widest mb-1.5" style={{ fontFamily: FONTS.mono, color: COLORS.slate, letterSpacing: "0.08em" }}>
                {label}
              </div>
              <div className="font-semibold" style={{ fontFamily: FONTS.display, fontSize: 19 }}>{value}</div>
            </div>
          ))}
          <div>
            <div className="text-xs uppercase tracking-widest mb-1.5" style={{ fontFamily: FONTS.mono, color: COLORS.slate, letterSpacing: "0.08em" }}>
              Run status
            </div>
            <div className="font-semibold" style={{ color: COLORS.good, fontSize: 15 }}>Completed</div>
          </div>
        </div>

        <div className="text-xs uppercase tracking-widest mb-3" style={{ fontFamily: FONTS.mono, color: COLORS.slate, letterSpacing: "0.08em" }}>
          Outputs
        </div>
        <div className="flex flex-wrap gap-2.5">
          {entry.outputs.map((o) => (
            <div key={o} className="flex items-center gap-2 text-xs px-4 py-2 rounded-full" style={{ fontFamily: FONTS.mono, background: COLORS.inkSoft, border: `1px solid ${COLORS.panelLine}` }}>
              <Dot /> {o}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
