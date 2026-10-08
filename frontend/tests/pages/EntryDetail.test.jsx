import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import EntryDetail from "../../src/pages/EntryDetail";

describe("EntryDetail", () => {
  it("renders comma-separated outputs returned by the backend", () => {
    render(
      <EntryDetail
        entry={{
          id: 12,
          connector: "SharePoint KB",
          mapper: "Knowledge Mapper",
          rules: "Knowledge Base Rules",
          outputs: "MongoDB, Kafka",
        }}
        goTo={vi.fn()}
      />,
    );

    expect(screen.getByText("MongoDB")).toBeInTheDocument();
    expect(screen.getByText("Kafka")).toBeInTheDocument();
  });
});
