/**
 * Unit tests for the `Configure` page (src/pages/Configure.jsx).
 *
 * `Configure` lists connectors, rules, and output targets, and lets the
 * user add or remove entries in each section via an inline "AddModal".
 * These tests verify:
 *   - A loading state is shown while `configLoading` is true.
 *   - Each section renders its items and the correct item count.
 *   - Opening the add-modal, typing a name, and submitting calls `addRow`
 *     with the right section key and trimmed name — and that submission is
 *     blocked for blank/whitespace-only input.
 *   - Clicking "Delete" on a row calls `removeConfigRow` with the right
 *     section key, id, and name.
 */
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import Configure from "../../src/pages/Configure";

const CONFIG = {
  connectors: [{ id: 1, name: "Infor Sales" }, { id: 2, name: "Jira Support" }],
  rules: [{ id: 3, name: "Infor Sales Rules" }],
  outputs: [],
};

describe("Configure", () => {
  //checks if the Configure page shows a loading message instead of the sections while configLoading is true
  it("shows a loading message instead of the sections while configLoading is true", () => {
    render(<Configure config={CONFIG} configLoading={true} addRow={vi.fn()} removeConfigRow={vi.fn()} />);

    expect(screen.getByText(/loading configuration/i)).toBeInTheDocument();
    expect(screen.queryByText("Infor Sales")).not.toBeInTheDocument();
  });

  //checks if the Configure page renders each section with its items and item count
  it("renders each section with its items and item count", () => {
    render(<Configure config={CONFIG} configLoading={false} addRow={vi.fn()} removeConfigRow={vi.fn()} />);

    expect(screen.getByText("Connectors")).toBeInTheDocument();
    expect(screen.getByText("Infor Sales")).toBeInTheDocument();
    expect(screen.getByText("Jira Support")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument(); // connectors count badge

    expect(screen.getByText("Rules")).toBeInTheDocument();
    expect(screen.getByText("Output Targets")).toBeInTheDocument();
    expect(screen.getByText("0")).toBeInTheDocument(); // outputs count badge
  });

  //checks if the Configure page opens the Add Connector modal and submits a trimmed name via addRow
  it("opens the Add Connector modal and submits a trimmed name via addRow", async () => {
    const user = userEvent.setup();
    const addRow = vi.fn();

    render(<Configure config={CONFIG} configLoading={false} addRow={addRow} removeConfigRow={vi.fn()} />);

    await user.click(screen.getByText("+ Add Connector"));
    expect(screen.getByText("Add Connector")).toBeInTheDocument();

    const input = screen.getByPlaceholderText("Connector name…");
    await user.type(input, "  SharePoint KB  ");
    await user.click(screen.getByRole("button", { name: "Add" }));

    expect(addRow).toHaveBeenCalledWith("connectors", "SharePoint KB");
    // The modal should close again after a successful submit.
    expect(screen.queryByText("Add Connector")).not.toBeInTheDocument();
  });

  //checks if the Configure page disables the Add button and blocks submission for blank/whitespace-only input
  it("disables the Add button and blocks submission for blank/whitespace-only input", async () => {
    const user = userEvent.setup();
    const addRow = vi.fn();

    render(<Configure config={CONFIG} configLoading={false} addRow={addRow} removeConfigRow={vi.fn()} />);

    await user.click(screen.getByText("+ Add Connector"));

    const addButton = screen.getByRole("button", { name: "Add" });
    expect(addButton).toBeDisabled();

    await user.type(screen.getByPlaceholderText("Connector name…"), "   ");
    expect(addButton).toBeDisabled();
    expect(addRow).not.toHaveBeenCalled();
  });

  //checks if the Configure page closes the modal without calling addRow when Cancel is clicked
  it("closes the modal without calling addRow when Cancel is clicked", async () => {
    const user = userEvent.setup();
    const addRow = vi.fn();

    render(<Configure config={CONFIG} configLoading={false} addRow={addRow} removeConfigRow={vi.fn()} />);

    await user.click(screen.getByText("+ Add Rule"));
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(screen.queryByText("Add Rule")).not.toBeInTheDocument();
    expect(addRow).not.toHaveBeenCalled();
  });

  //checks if the Configure page calls removeConfigRow with the section key, id, and name when Delete is clicked
  it("calls removeConfigRow with the section key, id, and name when Delete is clicked", async () => {
    const user = userEvent.setup();
    const removeConfigRow = vi.fn();

    render(<Configure config={CONFIG} configLoading={false} addRow={vi.fn()} removeConfigRow={removeConfigRow} />);

    const deleteButtons = screen.getAllByRole("button", { name: "Delete" });
    await user.click(deleteButtons[0]); // "Infor Sales" is the first connector row

    expect(removeConfigRow).toHaveBeenCalledWith("connectors", 1, "Infor Sales");
  });
});
