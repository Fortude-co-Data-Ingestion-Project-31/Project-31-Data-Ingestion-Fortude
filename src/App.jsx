import React, { useState, useRef, useEffect } from "react";
import { COLORS, FONTS, GOOGLE_FONTS_IMPORT } from "./theme";
import { INITIAL_HISTORY, INITIAL_CONFIG } from "./data";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import PageBadge from "./components/PageBadge";
import Toast from "./components/Toast";
import Dashboard from "./pages/Dashboard";
import NewIngestion from "./pages/NewIngestion";
import Configure from "./pages/Configure";
import History from "./pages/History";
import EntryDetail from "./pages/EntryDetail";

const PAGE_LABELS = {
  dashboard: "Dashboard Page",
  ingest: "Ingest Page",
  history: "History Page",
  configure: "Configuration Page",
  entry: "Ingestion Entry Page",
};

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [history, setHistory] = useState(INITIAL_HISTORY);
  const [config, setConfig] = useState(INITIAL_CONFIG);
  const [nextId, setNextId] = useState(7);
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
    <div style={{ background: COLORS.bg, fontFamily: FONTS.body, minHeight: "100vh" }}>
      <style>{`
        ${GOOGLE_FONTS_IMPORT}
        body { margin: 0; }
        select:focus { outline: none; border-color: ${COLORS.blue} !important; }
      `}</style>

      <PageBadge label={PAGE_LABELS[page]} />

      <div className="flex rounded-xl overflow-hidden mx-6 mb-6" style={{ border: `1px solid ${COLORS.border}`, background: COLORS.bg }}>
        <Sidebar page={page} goTo={goTo} />

        <div className="flex-1 min-w-0">
          <Header notificationCount={3} />

          <div className="px-8 py-8">
            {page === "dashboard" && <Dashboard history={history} config={config} goTo={goTo} openEntry={openEntry} />}
            {page === "ingest" && <NewIngestion form={form} setForm={setForm} onStart={startIngestion} />}
            {page === "configure" && <Configure config={config} addRow={addRow} removeConfigRow={removeConfigRow} />}
            {page === "history" && <History history={history} openEntry={openEntry} deleteEntry={deleteEntry} />}
            {page === "entry" && <EntryDetail entry={activeEntry} goTo={goTo} />}
          </div>
        </div>
      </div>

      <Toast message={toast} />
    </div>
  );
}
