import React, { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { API_BASE } from "../data";
import { COLORS } from "../theme";
import PageHeading from "../components/PageHeading";

const PAGE_SIZE = 50;

function formatMetadata(value) {
  if (value == null) return "";
  return typeof value === "string" ? value : JSON.stringify(value);
}

export default function VectorData() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [target, setTarget] = useState("");
  const [source, setSource] = useState("");
  const [offset, setOffset] = useState(0);
  const [reload, setReload] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({
      limit: String(PAGE_SIZE),
      offset: String(offset),
    });
    if (source) params.set("source", source);

    setLoading(true);
    setError("");
    fetch(`${API_BASE}/api/vector-documents?${params}`, {
      signal: controller.signal,
    })
      .then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(
            data.detail || `Unable to load vector data (HTTP ${response.status}).`
          );
        }
        return data;
      })
      .then((data) => {
        setItems(data.items);
        setTotal(data.total);
        setTarget(`${data.database}.${data.collection}`);
      })
      .catch((requestError) => {
        if (!controller.signal.aborted) {
          setError(requestError.message || "Unable to load vector data.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [offset, source, reload]);

  const changeSource = (event) => {
    setSource(event.target.value);
    setOffset(0);
  };

  return (
    <section>
      <PageHeading
        title="Vector Data"
        subtitle="Browse text chunks and metadata stored in the MongoDB vector database."
      />

      <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
        <label className="flex items-center gap-2 text-sm" style={{ color: COLORS.textMuted }}>
          Source
          <select
            aria-label="Filter by source"
            value={source}
            onChange={changeSource}
            className="rounded-md px-3 py-2"
            style={{
              color: COLORS.text,
              background: COLORS.card,
              border: `1px solid ${COLORS.border}`,
            }}
          >
            <option value="">All sources</option>
            <option value="sharepoint">SharePoint</option>
            <option value="jira">Jira</option>
            <option value="infor_m3">Infor</option>
            <option value="local_folder">Local files</option>
          </select>
        </label>
        <button
          type="button"
          onClick={() => setReload((value) => value + 1)}
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium disabled:opacity-50"
          style={{ color: COLORS.blue, background: COLORS.blueSoft }}
        >
          <RefreshCw size={15} />
          Refresh
        </button>
      </div>

      <div aria-live="polite" className="mb-3 text-sm" style={{ color: COLORS.textMuted }}>
        {loading
          ? "Loading vector data…"
          : `${total} chunk${total === 1 ? "" : "s"} stored in ${target}`}
      </div>

      {error && (
        <div
          role="alert"
          className="mb-4 rounded-lg p-4 text-sm"
          style={{ color: COLORS.red, background: "#fee2e2", border: "1px solid #fca5a5" }}
        >
          {error}
          <div className="mt-2">
            Check that the backend is configured with your Atlas `MONGO_URI` and
            `MONGO_DB_NAME`, and that your cluster allows this machine’s IP.
          </div>
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <div
          className="rounded-lg p-8 text-center text-sm"
          style={{ color: COLORS.textMuted, background: COLORS.card, border: `1px solid ${COLORS.border}` }}
        >
          No vector chunks found. Run an ingestion with MongoDB Vector Database selected.
        </div>
      )}

      <div className="grid gap-4">
        {items.map((item) => (
          <article
            key={item.record_id}
            className="rounded-lg p-5"
            style={{ color: COLORS.text, background: COLORS.card, border: `1px solid ${COLORS.border}` }}
          >
            <div className="flex flex-wrap items-start justify-between gap-2 mb-3">
              <div>
                <h2 className="font-semibold">{item.title || item.document_id}</h2>
                <div className="mt-1 text-xs" style={{ color: COLORS.textMuted }}>
                  {item.source} · {item.document_id} · chunk {item.chunk_index ?? item.chunk_id}
                </div>
              </div>
              {item.source_url && (
                <a
                  href={item.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm font-medium"
                  style={{ color: COLORS.blue }}
                >
                  Open source
                </a>
              )}
            </div>
            <p className="whitespace-pre-wrap break-words text-sm leading-6">
              {item.content}
            </p>
            <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs" style={{ color: COLORS.textMuted }}>
              {item.mapper && <span>Mapper: {item.mapper}</span>}
              {item.rule_applied && <span>Rule: {item.rule_applied}</span>}
              {item.kb_category && <span>Category: {item.kb_category}</span>}
              {item.kb_status && <span>Status: {item.kb_status}</span>}
              {item.tags?.length > 0 && <span>Tags: {item.tags.join(", ")}</span>}
              {item.page != null && <span>Page: {item.page}</span>}
              {item.slide != null && <span>Slide: {item.slide}</span>}
              {item.sheet && <span>Sheet: {item.sheet}</span>}
              {item.metadata && Object.keys(item.metadata).length > 0 && (
                <span>Metadata: {formatMetadata(item.metadata)}</span>
              )}
            </div>
          </article>
        ))}
      </div>

      {total > PAGE_SIZE && (
        <div className="mt-5 flex items-center justify-between">
          <button
            type="button"
            disabled={offset === 0 || loading}
            onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}
            className="rounded-md px-4 py-2 text-sm disabled:opacity-50"
            style={{ color: COLORS.text, background: COLORS.card, border: `1px solid ${COLORS.border}` }}
          >
            Previous
          </button>
          <span className="text-sm" style={{ color: COLORS.textMuted }}>
            {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
          </span>
          <button
            type="button"
            disabled={offset + PAGE_SIZE >= total || loading}
            onClick={() => setOffset((value) => value + PAGE_SIZE)}
            className="rounded-md px-4 py-2 text-sm disabled:opacity-50"
            style={{ color: COLORS.text, background: COLORS.card, border: `1px solid ${COLORS.border}` }}
          >
            Next
          </button>
        </div>
      )}
    </section>
  );
}
