import React from "react";
import Card from "../components/Card";
import Row from "../components/Row";
import PageHeading from "../components/PageHeading";

const SECTIONS = [
  ["connectors", "Connectors", "Connector"],
  ["rules", "Rules", "Rule"],
  ["outputs", "Output targets", "Output Target"],
];

export default function Configure({ config, addRow, removeConfigRow }) {
  return (
    <section>
      <PageHeading
        eyebrow="// building blocks"
        title="Configurations"
        subtitle="The connectors, rules, and output targets available when you build a new ingestion."
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {SECTIONS.map(([key, title, prefix]) => (
          <Card key={key} title={title} chip={String(config[key].length)} footer="+ Add" onFooterClick={() => addRow(key, prefix)}>
            <div style={{ maxHeight: 420, overflowY: "auto" }}>
              {config[key].map((label, i) => (
                <Row key={label} label={label} onDelete={() => removeConfigRow(key, i)} />
              ))}
            </div>
          </Card>
        ))}
      </div>
    </section>
  );
}
