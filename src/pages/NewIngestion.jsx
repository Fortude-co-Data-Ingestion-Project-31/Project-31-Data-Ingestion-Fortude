import React from "react";
import { COLORS, FONTS } from "../theme";
import { CONNECTOR_OPTIONS, MAPPER_OPTIONS, RULES_OPTIONS, OUTPUT_OPTIONS } from "../data";
import Select from "../components/Select";
import PageHeading from "../components/PageHeading";

export default function NewIngestion({ form, setForm, onStart }) {
  const { connector, mapper, rules, outputs } = form;
  const allFilled = connector && mapper && rules && outputs;

  const fields = [
    ["Select Connector", "connector", connector, CONNECTOR_OPTIONS],
    ["Select Mapper", "mapper", mapper, MAPPER_OPTIONS],
    ["Select Rules", "rules", rules, RULES_OPTIONS],
    ["Select Outputs", "outputs", outputs, OUTPUT_OPTIONS],
  ];

  return (
    <section>
      <PageHeading
        eyebrow="// new run"
        title="New Data Ingestion"
        subtitle="Wire a connector to a mapper, apply rules, and send the result wherever it needs to go."
      />

      {/* Pipeline signature */}
      <div className="relative flex items-center justify-between rounded-md px-8 py-6 mb-9" style={{ background: COLORS.inkSoft, border: `1px solid ${COLORS.panelLine}` }}>
        <div className="absolute h-0.5" style={{ top: 33, left: 60, right: 60, background: COLORS.panelLine, zIndex: 1 }} />
        {fields.map(([label, key, val]) => (
          <div key={key} className="flex flex-col items-center gap-2.5 flex-1 relative" style={{ zIndex: 2 }}>
            <div
              className="rounded-full transition-all"
              style={{
                width: 15,
                height: 15,
                background: val ? COLORS.signal : COLORS.ink,
                border: `2px solid ${val ? COLORS.signal : COLORS.panelLine}`,
                boxShadow: val ? "0 0 12px rgba(232,163,61,0.6)" : "none",
              }}
            />
            <div className="text-xs uppercase tracking-wide" style={{ fontFamily: FONTS.mono, letterSpacing: "0.08em", color: val ? COLORS.signal : COLORS.slate }}>
              {label.replace("Select ", "")}
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-md p-9" style={{ background: COLORS.panel, border: `1px solid ${COLORS.panelLine}` }}>
        <div className="grid gap-6" style={{ gridTemplateColumns: "180px 1fr" }}>
          {fields.map(([label, key, val, opts]) => (
            <React.Fragment key={key}>
              <label className="font-semibold text-sm self-center" style={{ fontFamily: FONTS.display }}>{label}</label>
              <Select value={val} onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))} options={opts} placeholder="Select from the following options" />
            </React.Fragment>
          ))}
        </div>
        <div className="flex justify-end mt-8">
          <button
            disabled={!allFilled}
            onClick={onStart}
            className="font-semibold text-sm px-6 py-3.5 rounded border-none"
            style={{
              fontFamily: FONTS.display,
              background: allFilled ? COLORS.signal : COLORS.panelLine,
              color: allFilled ? "#1a1305" : COLORS.slate,
              cursor: allFilled ? "pointer" : "not-allowed",
            }}
          >
            Start
          </button>
        </div>
      </div>
    </section>
  );
}
