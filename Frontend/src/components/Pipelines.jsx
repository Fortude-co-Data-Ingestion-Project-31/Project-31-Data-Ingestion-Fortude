import React, { useEffect, useState } from "react";
import { API_BASE } from "../data";
import Card from "./Card";

const FIELD_STYLE =
  "w-full rounded-lg border border-[color:var(--border)] bg-[color:var(--bg)] px-3 py-2 text-[color:var(--text)]";
const BUTTON_STYLE =
  "rounded-lg bg-[color:var(--blue)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-40 disabled:cursor-not-allowed";

export default function Pipelines({ config }) {
  const [pipelines, setPipelines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [reload, setReload] = useState(0);
  const [creating, setCreating] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [name, setName] = useState("");
  const [connectorId, setConnectorId] = useState("");
  const [ruleIds, setRuleIds] = useState([]);
  const [outputIds, setOutputIds] = useState([]);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    async function loadPipelines() {
      setLoading(true);
      setLoadError("");
      try {
        const response = await fetch(`${API_BASE}/api/config/pipelines`, {
          signal: controller.signal,
        });
        if (!response.ok) throw new Error("Unable to load pipelines.");
        const data = await response.json();
        if (!controller.signal.aborted) setPipelines(data);
      } catch (error) {
        if (!controller.signal.aborted)
          setLoadError("Unable to load pipelines. Please try again.");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    loadPipelines();
    return () => controller.abort();
  }, [reload]);

  const hasChoices =
    config.connectors.length > 0 &&
    config.rules.length > 0 &&
    config.outputs.length > 0;

  // frontend validation before save button is enabled for user
  const valid =
    name.trim() &&
    config.connectors.some((item) => item.id === Number(connectorId)) &&
    ruleIds.length > 0 &&
    ruleIds.every((id) => config.rules.some((item) => item.id === id)) &&
    outputIds.length > 0 &&
    outputIds.every((id) => config.outputs.some((item) => item.id === id));

  // for checkboxes
  function toggleSelection(setIds, id) {
    setIds((ids) =>
      ids.includes(id)
        ? ids.filter((selected) => selected !== id)
        : [...ids, id]
    );
  }

  function closeForm() {
    setCreating(false);
    setEditingId(null);
    setName("");
    setConnectorId("");
    setRuleIds([]);
    setOutputIds([]);
    setSaveError("");
  }

  // loads existing pipeline into form so it can be edited
  function editPipeline(pipeline) {
    setEditingId(pipeline.id);
    setName(pipeline.name);
    setConnectorId(String(pipeline.connector.id));
    setRuleIds(pipeline.rules.map((item) => item.id));
    setOutputIds(pipeline.outputs.map((item) => item.id));
    setSaveError("");
    setNotice("");
  }

  // store pipeline using POST or PUT depending on whether it's a new pipeline or an edit
  async function savePipeline(event) {
    event.preventDefault();
    if (!valid || saving) return;
    setSaving(true);
    setSaveError("");
    try {
      const url =
        editingId === null
          ? `${API_BASE}/api/config/pipelines`
          : `${API_BASE}/api/config/pipelines/${editingId}`;
      const response = await fetch(url, {
        method: editingId === null ? "POST" : "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          connector_id: Number(connectorId),
          rule_ids: ruleIds,
          output_ids: outputIds,
        }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const message =
          typeof body.detail === "string"
            ? body.detail
            : "Could not save pipeline. Check your selections and try again.";
        throw new Error(message);
      }
      const pipeline = await response.json();
      setPipelines((items) =>
        editingId === null
          ? [...items, pipeline]
          : items.map((item) => (item.id === editingId ? pipeline : item))
      );
      closeForm();
      setNotice(`Pipeline "${pipeline.name}" saved.`);
    } catch (error) {
      setSaveError(
        error.message || "Could not save pipeline. Please try again."
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card
      title="Pipelines"
      count={loading || loadError ? undefined : pipelines.length}
    >
      <div className="p-6 space-y-4 text-sm text-[color:var(--text)]">
        {loading ? (
          <p role="status">Loading pipelines...</p>
        ) : loadError ? (
          <div role="alert">
            <p>{loadError}</p>
            <button
              type="button"
              className={BUTTON_STYLE}
              onClick={() => setReload((value) => value + 1)}
            >
              Retry
            </button>
          </div>
        ) : (
          <>
            {pipelines.length === 0 ? (
              <p>No saved pipelines yet.</p>
            ) : (
              <ul className="space-y-3">
                {pipelines.map((pipeline) => (
                  <li
                    key={pipeline.id}
                    className="rounded-lg border border-[color:var(--border)] p-4 space-y-1 break-words"
                  >
                    <h4 className="font-semibold">{pipeline.name}</h4>
                    <p>Connector: {pipeline.connector.name}</p>
                    <p>
                      Rules:{" "}
                      {pipeline.rules.map((item) => item.name).join(", ")}
                    </p>
                    <p>
                      Outputs:{" "}
                      {pipeline.outputs.map((item) => item.name).join(", ")}
                    </p>
                    <button
                      type="button"
                      className={BUTTON_STYLE}
                      disabled={creating || editingId !== null || saving}
                      aria-label={`Edit ${pipeline.name}`}
                      onClick={() => editPipeline(pipeline)}
                    >
                      Edit
                    </button>
                  </li>
                ))}
              </ul>
            )}
            {notice && <p role="status">{notice}</p>}
            {!hasChoices && (
              <p>
                Add at least one connector, rule, and output target before
                creating a pipeline.
              </p>
            )}
            {!creating && editingId === null ? (
              <button
                type="button"
                className={BUTTON_STYLE}
                disabled={!hasChoices}
                onClick={() => {
                  setCreating(true);
                  setNotice("");
                }}
              >
                Create pipeline
              </button>
            ) : (
              <form
                aria-label={
                  editingId === null ? "Create pipeline" : "Edit pipeline"
                }
                onSubmit={savePipeline}
                className="space-y-4 border-t border-[color:var(--border)] pt-4"
              >
                <h4 className="font-semibold">
                  {editingId === null ? "Create pipeline" : "Edit pipeline"}
                </h4>
                <fieldset disabled={saving} className="space-y-4">
                  <label className="block">
                    Pipeline name
                    <input
                      autoFocus
                      required
                      className={FIELD_STYLE}
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                    />
                  </label>
                  <label className="block">
                    Connector
                    <select
                      required
                      className={FIELD_STYLE}
                      value={connectorId}
                      onChange={(event) => setConnectorId(event.target.value)}
                    >
                      <option value="">Select a connector</option>
                      {config.connectors.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <fieldset>
                    <legend className="font-semibold mb-2">
                      Rules (select at least one)
                    </legend>
                    {config.rules.map((item) => (
                      <label
                        key={item.id}
                        className="flex items-center gap-2 py-1"
                      >
                        <input
                          type="checkbox"
                          checked={ruleIds.includes(item.id)}
                          onChange={() => toggleSelection(setRuleIds, item.id)}
                        />
                        {item.name}
                      </label>
                    ))}
                  </fieldset>
                  <fieldset>
                    <legend className="font-semibold mb-2">
                      Outputs (select at least one)
                    </legend>
                    {config.outputs.map((item) => (
                      <label
                        key={item.id}
                        className="flex items-center gap-2 py-1"
                      >
                        <input
                          type="checkbox"
                          checked={outputIds.includes(item.id)}
                          onChange={() =>
                            toggleSelection(setOutputIds, item.id)
                          }
                        />
                        {item.name}
                      </label>
                    ))}
                  </fieldset>
                  {saveError && <p role="alert">{saveError}</p>}
                  <div className="flex gap-3">
                    <button
                      type="submit"
                      className={BUTTON_STYLE}
                      disabled={!valid || saving}
                    >
                      {saving ? "Saving..." : "Save pipeline"}
                    </button>
                    <button
                      type="button"
                      className="rounded-lg border border-[color:var(--border)] px-4 py-2"
                      onClick={closeForm}
                    >
                      Cancel
                    </button>
                  </div>
                </fieldset>
              </form>
            )}
          </>
        )}
      </div>
    </Card>
  );
}
