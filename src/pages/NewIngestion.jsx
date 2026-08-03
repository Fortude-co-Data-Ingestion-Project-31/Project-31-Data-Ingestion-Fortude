import React from "react";
import { COLORS } from "../theme";
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
      <PageHeading title="New Data Ingestion" subtitle="Wire a connector to a mapper, apply rules, and send the result to an output target." />

      {/* Pipeline indicator */}
      <div className="relative flex items-center justify-between rounded-lg px-8 py-6 mb-6" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}>
        <div className="absolute h-0.5" style={{ top: 33, left: 60, right: 60, background: COLORS.border, zIndex: 1 }} />
        {fields.map(([label, key, val]) => (
          <div key={key} className="flex flex-col items-center gap-2.5 flex-1 relative" style={{ zIndex: 2 }}>
            <div
              className="rounded-full transition-all"
              style={{
                width: 14,
                height: 14,
                background: val ? COLORS.orange : "#ffffff",
                border: `2px solid ${val ? COLORS.orange : COLORS.border}`,
              }}
            />
            <div className="text-xs font-medium" style={{ color: val ? COLORS.orange : COLORS.textFaint }}>
              {label.replace("Select ", "")}
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-lg p-8" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}>
        <div className="grid gap-6" style={{ gridTemplateColumns: "180px 1fr" }}>
          {fields.map(([label, key, val, opts]) => (
            <React.Fragment key={key}>
              <label className="font-semibold text-sm self-center" style={{ color: COLORS.text }}>{label}</label>
              <Select value={val} onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))} options={opts} placeholder="Select from the following options" />
            </React.Fragment>
          ))}
        </div>
        <div className="flex justify-end mt-8">
          <button
            disabled={!allFilled}
            onClick={onStart}
            className="font-semibold text-sm px-6 py-2.5 rounded-md border-none text-white"
            style={{
              background: allFilled ? COLORS.orange : COLORS.badgeBg,
              color: allFilled ? "#ffffff" : COLORS.textFaint,
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
