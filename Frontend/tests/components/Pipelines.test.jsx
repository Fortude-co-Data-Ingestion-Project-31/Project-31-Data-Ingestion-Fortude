import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, describe, it, vi } from "vitest";
import Pipelines from "../../src/components/Pipelines";
import { API_BASE } from "../../src/data";

const CONFIG = {
  connectors: [{ id: 2, name: "Jira" }],
  rules: [
    { id: 2, name: "L3 Ticket Rules" },
    { id: 3, name: "Knowledge Base Rules" },
  ],
  outputs: [
    { id: 1, name: "MongoDB" },
    { id: 3, name: "Kafka" },
  ],
};

// test pipeline
const PIPELINE = {
  id: 10,
  name: "Test Pipeline",
  connector: CONFIG.connectors[0],
  rules: CONFIG.rules,
  outputs: CONFIG.outputs,
};

describe("Pipelines", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => [] })
    );
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  // Check the loading message and the saved pipeline details.
  it("loads saved pipelines and displays expanded reference names", async () => {
    fetch.mockResolvedValueOnce({ ok: true, json: async () => [PIPELINE] });
    render(<Pipelines config={CONFIG} />);
    expect(screen.getByText(/Loading pipelines/)).toBeInTheDocument();
    expect(await screen.findByText("Test Pipeline")).toBeInTheDocument();
    expect(screen.getByText("Connector: Jira")).toBeInTheDocument();
    expect(
      screen.getByText("Rules: L3 Ticket Rules, Knowledge Base Rules")
    ).toBeInTheDocument();
    expect(screen.getByText("Outputs: MongoDB, Kafka")).toBeInTheDocument();
  });

  // Save stays disabled until all required fields are valid.
  it("requires a name, connector, rule, and output before saving", async () => {
    const user = userEvent.setup();
    render(<Pipelines config={CONFIG} />);
    await user.click(
      await screen.findByRole("button", { name: "Create pipeline" })
    );
    const save = screen.getByRole("button", { name: "Save pipeline" });
    expect(save).toBeDisabled();
    await user.type(screen.getByLabelText("Pipeline name"), "   ");
    await user.selectOptions(screen.getByLabelText("Connector"), "2");
    await user.click(screen.getByLabelText("L3 Ticket Rules"));
    await user.click(screen.getByLabelText("Kafka"));
    expect(save).toBeDisabled();
    await user.type(screen.getByLabelText("Pipeline name"), "Test Pipeline");
    expect(save).toBeEnabled();
    await user.click(screen.getByLabelText("L3 Ticket Rules"));
    expect(save).toBeDisabled();
  });

  // Send the selected IDs and display the pipeline returned by the backend.
  it("posts numeric IDs and adds the saved pipeline to the list", async () => {
    const user = userEvent.setup();
    render(<Pipelines config={CONFIG} />);
    await user.click(
      await screen.findByRole("button", { name: "Create pipeline" })
    );
    await user.type(screen.getByLabelText("Pipeline name"), " Test Pipeline ");
    await user.selectOptions(screen.getByLabelText("Connector"), "2");
    await user.click(screen.getByLabelText("L3 Ticket Rules"));
    await user.click(screen.getByLabelText("Knowledge Base Rules"));
    await user.click(screen.getByLabelText("MongoDB"));
    await user.click(screen.getByLabelText("Kafka"));
    fetch.mockResolvedValueOnce({ ok: true, json: async () => PIPELINE });
    await user.click(screen.getByRole("button", { name: "Save pipeline" }));
    expect(fetch).toHaveBeenLastCalledWith(`${API_BASE}/api/config/pipelines`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: "Test Pipeline",
        connector_id: 2,
        rule_ids: [2, 3],
        output_ids: [1, 3],
      }),
    });
    expect(await screen.findByText("Test Pipeline")).toBeInTheDocument();
    expect(screen.queryByRole("form")).not.toBeInTheDocument();
  });

  // A failed save should keep the selections so the user can correct them.
  it("preserves input after a save error and allows retry", async () => {
    const user = userEvent.setup();
    render(<Pipelines config={CONFIG} />);
    await user.click(
      await screen.findByRole("button", { name: "Create pipeline" })
    );
    await user.type(screen.getByLabelText("Pipeline name"), "Test Pipeline");
    await user.selectOptions(screen.getByLabelText("Connector"), "2");
    await user.click(screen.getByLabelText("L3 Ticket Rules"));
    await user.click(screen.getByLabelText("Kafka"));
    fetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: "Pipeline already exists" }),
    });
    await user.click(screen.getByRole("button", { name: "Save pipeline" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Pipeline already exists"
    );
    expect(screen.getByLabelText("Pipeline name")).toHaveValue("Test Pipeline");
    expect(screen.getByLabelText("L3 Ticket Rules")).toBeChecked();
    expect(screen.getByRole("button", { name: "Save pipeline" })).toBeEnabled();
  });

  // A failed load can be retried without leaving the page.
  it("shows a retry action when loading fails", async () => {
    const user = userEvent.setup();
    fetch.mockRejectedValueOnce(new Error("offline"));
    render(<Pipelines config={CONFIG} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unable to load pipelines"
    );
    await user.click(screen.getByRole("button", { name: "Retry" }));
    expect(
      await screen.findByText("No saved pipelines yet.")
    ).toBeInTheDocument();
  });

  // Cancel discards the draft without sending a save request.
  it("cancels without posting and clears the form", async () => {
    const user = userEvent.setup();
    render(<Pipelines config={CONFIG} />);
    await user.click(
      await screen.findByRole("button", { name: "Create pipeline" })
    );
    await user.type(screen.getByLabelText("Pipeline name"), "Discard me");
    await user.click(screen.getByRole("button", { name: "Cancel" }));
    await user.click(screen.getByRole("button", { name: "Create pipeline" }));
    expect(screen.getByLabelText("Pipeline name")).toHaveValue("");
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  // Keep the save request pending to check that controls are disabled.
  it("disables the form while a save is pending", async () => {
    const user = userEvent.setup();
    render(<Pipelines config={CONFIG} />);
    await user.click(
      await screen.findByRole("button", { name: "Create pipeline" })
    );
    await user.type(screen.getByLabelText("Pipeline name"), "Test Pipeline");
    await user.selectOptions(screen.getByLabelText("Connector"), "2");
    await user.click(screen.getByLabelText("L3 Ticket Rules"));
    await user.click(screen.getByLabelText("Kafka"));
    // Resolve this request after checking the saving state.
    let finishSave;
    fetch.mockReturnValueOnce(
      new Promise((resolve) => {
        finishSave = resolve;
      })
    );
    await user.click(screen.getByRole("button", { name: "Save pipeline" }));
    expect(screen.getByRole("button", { name: /Saving/ })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeDisabled();
    finishSave({ ok: true, json: async () => PIPELINE });
    await waitFor(() =>
      expect(screen.queryByRole("form")).not.toBeInTheDocument()
    );
  });
});
