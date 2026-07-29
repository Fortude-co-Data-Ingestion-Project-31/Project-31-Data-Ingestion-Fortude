import React, { useState, useRef, useEffect } from "react";
import { COLORS, FONTS, GOOGLE_FONTS_IMPORT } from "./theme";
import { INITIAL_HISTORY, INITIAL_CONFIG } from "./data";
import TopBar from "./components/TopBar";
import Toast from "./components/Toast";
import Dashboard from "./pages/Dashboard";
import NewIngestion from "./pages/NewIngestion";
import Configure from "./pages/Configure";
import History from "./pages/History";
import EntryDetail from "./pages/EntryDetail";

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [history, setHistory] = useState(INITIAL_HISTORY);
  const [config, setConfig] = useState(INITIAL_CONFIG);
  const [nextId, setNextId] = useState(9);
  const [activeEntryId, setActiveEntryId] = useState(1);
  const [toast, setToast] = useState("");
  const toastTimer = useRef(null);

  const [form, setForm] = useState({ connector: "", mapper: "", rules: "", outputs: "" });

  const showToast = (msg) => {
    setToast(msg);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(""), 2200);
  };

  useEffect(() => () => clearTimeout(toastTimer.current), []);

  const goTo = (p) => {
    setPage(p);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const openEntry = (id) => {
    setActiveEntryId(id);
    goTo("entry");
  };

  const deleteEntry = (id) => {
    setHistory((h) => h.filter((e) => e.id !== id));
    showToast(`Entry ${id} deleted`);
  };

  const removeConfigRow = (key, idx) => {
    const label = config[key][idx];
    setConfig((c) => ({ ...c, [key]: c[key].filter((_, i) => i !== idx) }));
    showToast(`${label} deleted`);
  };

  const addRow = (key, prefix) => {
    setConfig((c) => {
      const n = c[key].length + 1;
      return { ...c, [key]: [...c[key], `${prefix} Entry ${n}`] };
    });
    showToast(`${prefix} Entry ${config[key].length + 1} added`);
  };

  const startIngestion = () => {
    const entry = { id: nextId, ...form, outputs: [form.outputs] };
    setHistory((h) => [...h, entry]);
    setNextId((n) => n + 1);
    showToast(`Ingestion started — Entry ${nextId}`);
    setForm({ connector: "", mapper: "", rules: "", outputs: "" });
    goTo("dashboard");
  };

  const activeEntry = history.find((e) => e.id === activeEntryId) || history[0];

  return (
    <div style={{ background: COLORS.ink, color: COLORS.paper, fontFamily: FONTS.body, minHeight: "100vh" }}>
      <style>{`
        ${GOOGLE_FONTS_IMPORT}
        select:focus { outline: none; border-color: ${COLORS.signal} !important; }
        ::selection { background: ${COLORS.signal}; color: ${COLORS.ink}; }
      `}</style>

      <TopBar page={page} goTo={goTo} />

      <div className="max-w-5xl mx-auto px-8 py-12 pb-24">
        {page === "dashboard" && <Dashboard history={history} config={config} goTo={goTo} openEntry={openEntry} />}
        {page === "ingest" && <NewIngestion form={form} setForm={setForm} onStart={startIngestion} />}
        {page === "configure" && <Configure config={config} addRow={addRow} removeConfigRow={removeConfigRow} />}
        {page === "history" && <History history={history} openEntry={openEntry} deleteEntry={deleteEntry} />}
        {page === "entry" && <EntryDetail entry={activeEntry} goTo={goTo} />}
      </div>

      <Toast message={toast} />
    </div>
  );
}
