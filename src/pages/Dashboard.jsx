import React from "react";
import { FONTS, COLORS } from "../theme";
import Card from "../components/Card";
import Row from "../components/Row";
import PageHeading from "../components/PageHeading";

export default function Dashboard({ history, config, goTo, openEntry }) {
  const dashboardEntries = history.slice(-5).reverse();
  const totalConfig = Object.values(config).reduce((a, b) => a + b.length, 0);

  return (
    <section>
      <PageHeading
        eyebrow="// overview"
        title="Dashboard"
        subtitle="Every pipeline your team has wired up, and the parts they're built from, in one place."
      />

      <div className="mb-12">
        <button
          onClick={() => goTo("ingest")}
          className="font-semibold text-sm px-6 py-3.5 rounded border-none cursor-pointer"
          style={{ fontFamily: FONTS.display, background: COLORS.signal, color: "#1a1305" }}
        >
          Start Ingestion
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-7">
        <Card title="Past Ingestions" chip={`${history.length} total`} footer="View all →" onFooterClick={() => goTo("history")}>
          {dashboardEntries.map((e) => (
            <Row key={e.id} label={`Entry ${e.id}`} sub={e.connector} onView={() => openEntry(e.id)} />
          ))}
        </Card>

        <Card title="Configurations" chip={`${totalConfig} total`} footer="View all →" onFooterClick={() => goTo("configure")}>
          <Row label="Connector Entry 1" onView={() => goTo("configure")} />
          <Row label="Rules Entry 1" onView={() => goTo("configure")} />
          <Row label="Output Target Entry 1" onView={() => goTo("configure")} />
          <Row label="Connector Entry 2" onView={() => goTo("configure")} />
          <Row label="Rules Entry 2" onView={() => goTo("configure")} />
        </Card>
      </div>
    </section>
  );
}
