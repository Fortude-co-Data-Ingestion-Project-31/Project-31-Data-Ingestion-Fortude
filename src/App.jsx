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

// A simple page-label map used by the badge component at the top of the app.
const PAGE_LABELS = {
  dashboard: "Dashboard Page",
  ingest: "Ingest Page",
  history: "History Page",
  configure: "Configuration Page",
  entry: "Ingestion Entry Page",
};

// The root app component controls navigation, shared state, and the main layout.
export default function App() {
  // Tracks which page is currently visible in the main content area.
  const [page, setPage] = useState("dashboard");
  // Controls whether the left-hand navigation panel is visible.
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // These states hold the prototype data shown across the dashboard, history, and configuration pages.
  const [history, setHistory] = useState(INITIAL_HISTORY);
  const [config, setConfig] = useState(INITIAL_CONFIG);
  const [nextId, setNextId] = useState(7);
  const [activeEntryId, setActiveEntryId] = useState(1);
  const [toast, setToast] = useState("");
  const toastTimer = useRef(null);

  // Form state for the ingestion creation page.
  const [form, setForm] = useState({ connector: "", mapper: "", rules: "", outputs: "" });

  // Displays a brief success or status message near the bottom of the screen.
  const showToast = (msg) => {
    setToast(msg);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(""), 2200);
  };

  useEffect(() => () => clearTimeout(toastTimer.current), []);

  // FUTURE BACKEND HOOK:
  // Replace these mock state initializers with real API requests once the backend is available.
  useEffect(() => {
    // Example:
    // fetch("/api/ingestions")
    //   .then((response) => response.json())
    //   .then((data) => setHistory(data))
    //   .catch(() => showToast("Unable to load ingestion history"));
  }, []);

  // Opens or closes the navigation drawer on smaller screens or when the user clicks the menu button.
  const toggleSidebar = () => setIsSidebarOpen((prev) => !prev);
  const closeSidebar = () => setIsSidebarOpen(false);

  // Switches the visible page and scrolls the content area back to the top.
  const goTo = (p) => {
    setPage(p);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  // Opens a specific ingestion entry in the detail view.
  const openEntry = (id) => {
    setActiveEntryId(id);
    goTo("entry");
  };

  // Removes an ingestion entry from the visible history list.
  const deleteEntry = (id) => {
    setHistory((h) => h.filter((e) => e.id !== id));
    showToast(`Entry ${id} deleted`);
  };

  // Deletes one row from a configuration category such as connectors or rules.
  const removeConfigRow = (key, idx) => {
    const label = config[key][idx];
    setConfig((c) => ({ ...c, [key]: c[key].filter((_, i) => i !== idx) }));
    showToast(`${label} deleted`);
  };

  // Adds a new item to a configuration list and updates the UI immediately.
  const addRow = (key, prefix) => {
    setConfig((c) => {
      const n = c[key].length + 1;
      return { ...c, [key]: [...c[key], `${prefix} Entry ${n}`] };
    });
    showToast(`${prefix} Entry ${config[key].length + 1} added`);
  };

  // Handles submission of a new ingestion request from the form page.
  const startIngestion = () => {
    // TODO: Replace this local state update with a POST request to the backend API.
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

      <div className="flex rounded-xl overflow-hidden mx-6 mb-6 relative" style={{ border: `1px solid ${COLORS.border}`, background: COLORS.bg }}>
        {isSidebarOpen && (
          <div className="fixed inset-0 z-20 bg-black/30 transition-opacity duration-200 md:hidden" onClick={closeSidebar} />
        )}

        <div className="relative z-30">
          {isSidebarOpen ? <Sidebar page={page} goTo={goTo} onClose={closeSidebar} /> : null}
        </div>

        <div className="flex-1 min-w-0">
          <Header notificationCount={3} onToggleSidebar={toggleSidebar} />

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
