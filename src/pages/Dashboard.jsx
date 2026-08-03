import React from "react";
import { COLORS } from "../theme";
import Card from "../components/Card";
import Row from "../components/Row";
import PageHeading from "../components/PageHeading";

// Dashboard page shows a high-level summary of recent ingestions and configuration items.
export default function Dashboard({ history, config, goTo, openEntry }) {
  // Shows the most recent five ingestion entries in reverse chronological order.
  const dashboardEntries = history.slice(-5).reverse();
  // Calculates the total number of configuration entries across all config groups.
  const totalConfig = Object.values(config).reduce((a, b) => a + b.length, 0);

  return (
    <section>
      <PageHeading title="Dashboard" subtitle="An overview of your ingestion pipelines and configuration." />

      <div className="mb-8">
        <button
          onClick={() => goTo("ingest")}
          className="font-semibold text-sm px-5 py-2.5 rounded-md border-none cursor-pointer text-white"
          style={{ background: COLORS.orange }}
        >
          Start Ingestion
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Past Ingestions" count={history.length} footer="View all →" onFooterClick={() => goTo("history")}>
          {dashboardEntries.map((e) => (
            <Row key={e.id} label={`Entry ${e.id}`} sub={e.connector} onEdit={() => openEntry(e.id)} />
          ))}
        </Card>

        <Card title="Configurations" count={totalConfig} footer="View all →" onFooterClick={() => goTo("configure")}>
          <Row label="Infor Sales" sub="Connector" onEdit={() => goTo("configure")} />
          <Row label="Infor Sales Rules" sub="Rule" onEdit={() => goTo("configure")} />
          <Row label="PostgreSQL" sub="Output" onEdit={() => goTo("configure")} />
          <Row label="Jira Support" sub="Connector" onEdit={() => goTo("configure")} />
          <Row label="L3 Ticket Rules" sub="Rule" onEdit={() => goTo("configure")} />
        </Card>
      </div>
    </section>
  );
}
