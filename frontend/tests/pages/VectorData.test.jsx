import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import VectorData from "../../src/pages/VectorData";

describe("VectorData", () => {
  it("loads and displays vector chunk text and metadata", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [{
          record_id: "sharepoint:guide:guide_0",
          source: "sharepoint",
          document_id: "guide",
          chunk_index: 0,
          title: "Guide",
          content: "A useful guide chunk.",
          mapper: "Custom JSON Mapper",
          rule_applied: "Knowledge Base Rules",
          tags: ["knowledge"],
        }],
        total: 1,
        limit: 50,
        offset: 0,
        database: "atlas_vectors",
        collection: "vector_chunks",
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<VectorData />);

    expect(await screen.findByText("A useful guide chunk.")).toBeInTheDocument();
    expect(screen.getByText(/Mapper: Custom JSON Mapper/)).toBeInTheDocument();
    expect(screen.getByText(/Rule: Knowledge Base Rules/)).toBeInTheDocument();
    expect(screen.getByText(/1 chunk stored in atlas_vectors\.vector_chunks/)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/vector-documents?"),
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );

    vi.unstubAllGlobals();
  });

  it("shows a backend connection error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Atlas unavailable")));

    render(<VectorData />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Atlas unavailable");
    vi.unstubAllGlobals();
  });
});
