import React from "react";
import Card from "../components/Card";
import Row from "../components/Row";
import PageHeading from "../components/PageHeading";

const SECTIONS = [
  ["connectors", "Connectors", "Connector"],
  ["rules", "Rules", "Rule"],
  ["outputs", "Output Targets", "Output Target"],
];

export default function Configure({ config, addRow, removeConfigRow }) {
  return (
    <section>
      <PageHeading title="Configuration" subtitle="Manage connectors, rules, and output targets." />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {SECTIONS.map(([key, title, prefix]) => (
          <Card key={key} title={title} count={config[key].length} footer={`+ Add ${prefix}`} onFooterClick={() => addRow(key, prefix)}>
            <div style={{ maxHeight: 420, overflowY: "auto" }}>
              {config[key].map((label, i) => (
                <Row key={label} label={label} onEdit={() => {}} onDelete={() => removeConfigRow(key, i)} />
              ))}
            </div>
          </Card>
        ))}
      </div>
    </section>
  );
}
