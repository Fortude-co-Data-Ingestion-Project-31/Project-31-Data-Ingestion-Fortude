import React, { useState, useRef, useEffect } from "react";
import { COLORS, FONTS, GOOGLE_FONTS_IMPORT, LIGHT_THEME, DARK_THEME } from "./theme";
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
import Login from "./pages/Login";
import Settings from "./pages/Settings";
import ChangeUsername from "./pages/ChangeUsername";

// A simple page-label map used by the badge component at the top of the app.
const PAGE_LABELS = {
  dashboard: "Dashboard Page",
  ingest: "Ingest Page",
  history: "History Page",
  configure: "Configuration Page",
  settings: "Settings",
  "change-username": "Change Username",
  entry: "Ingestion Entry Page",
};

// The root app component controls navigation, shared state, and the main layout.
export default function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [themeMode, setThemeMode] = useState("light");
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

  useEffect(() => {
    const storedTheme = localStorage.getItem("theme");
    if (storedTheme === "dark" || storedTheme === "light") {
      setThemeMode(storedTheme);
    }
  }, []);

  useEffect(() => {
    const theme = themeMode === "dark" ? DARK_THEME : LIGHT_THEME;
    Object.entries(theme).forEach(([key, value]) => {
      document.documentElement.style.setProperty(`--${key}`, value);
    });
    localStorage.setItem("theme", themeMode);
  }, [themeMode]);

  // FUTURE BACKEND HOOK:
  // Replace these mock state initializers with real API requests once the backend is available.
  useEffect(() => {
    // Example:
    // fetch("/api/ingestions")
    //   .then((response) => response.json())
    //   .then((data) => setHistory(data))
    //   .catch(() => showToast("Unable to load ingestion history"));
    // Check for stored token and verify with backend
    const token = localStorage.getItem("auth_token");
    if (token) {
      fetch("http://127.0.0.1:8000/api/auth/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      })
        .then((r) => {
          if (!r.ok) throw new Error("invalid token");
          return r.json();
        })
        .then((data) => {
          setAuthenticated(true);
          setCurrentUser(data.username);
        })
        .catch(() => {
          localStorage.removeItem("auth_token");
          setAuthenticated(false);
          setCurrentUser(null);
        });
    }
  }, []);

  // Opens or closes the navigation drawer on smaller screens or when the user clicks the menu button.
  const toggleSidebar = () => setIsSidebarOpen((prev) => !prev);
  const closeSidebar = () => setIsSidebarOpen(false);

  const signOut = () => {
    setAuthenticated(false);
    setCurrentUser(null);
    localStorage.removeItem("auth_token");
    goTo("dashboard");
  };

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
  const startIngestion = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8000/api/ingest/local-folder", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ connector: form.connector, rule: form.rules }),
      });

      if (!response.ok) {
        throw new Error("Ingestion request failed");
      }

      const data = await response.json();
      const entry = { id: nextId, ...form, outputs: [form.outputs] };
      setHistory((h) => [...h, entry]);
      setNextId((n) => n + 1);
      showToast(`Ingestion complete - ${data.processed} document(s) processed`);
      setForm({ connector: "", mapper: "", rules: "", outputs: "" });
      goTo("dashboard");
    } catch (error) {
      showToast("Ingestion failed. Please try again.");
    }
  };

  const activeEntry = history.find((e) => e.id === activeEntryId) || history[0];

  if (!authenticated) {
    return <Login onLogin={(username) => { setAuthenticated(true); setCurrentUser(username); }} />;
  }

  return (
    <div style={{ background: COLORS.bg, fontFamily: FONTS.body, minHeight: "100vh" }}>
      <style>{`
        ${GOOGLE_FONTS_IMPORT}
        body { margin: 0; }
        select:focus { outline: none; border-color: ${COLORS.blue} !important; }
      `}</style>

      <PageBadge label={PAGE_LABELS[page]} />

      <div className="flex rounded-xl overflow-hidden mx-6 mb-6 relative" style={{ border: `1px solid ${COLORS.border}`, background: COLORS.bg }}>
        {/* Sidebar overlay removed — sidebar now opens/closes only via hamburger */}

        <div className="relative z-30">
          {isSidebarOpen ? (
            <Sidebar page={page} goTo={goTo} user={currentUser} onSignOut={signOut} />
          ) : null}
        </div>

        <div className="flex-1 min-w-0">
          <Header
            notificationCount={3}
            onToggleSidebar={toggleSidebar}
            onOpenSettings={() => goTo("settings")}
            themeMode={themeMode}
            onToggleTheme={() => setThemeMode((prev) => (prev === "dark" ? "light" : "dark"))}
          />

          <div className="px-8 py-8">
            {page === "dashboard" && <Dashboard history={history} config={config} goTo={goTo} openEntry={openEntry} />}
            {page === "ingest" && <NewIngestion form={form} setForm={setForm} onStart={startIngestion} />}
            {page === "configure" && <Configure config={config} addRow={addRow} removeConfigRow={removeConfigRow} />}
            {page === "settings" && <Settings token={localStorage.getItem("auth_token")} currentUser={currentUser} onSaved={(username) => setCurrentUser(username)} goTo={goTo} />}
            {page === "change-username" && <ChangeUsername token={localStorage.getItem("auth_token")} currentUser={currentUser} onSaved={(username) => setCurrentUser(username)} goTo={goTo} />}
            {page === "history" && <History history={history} openEntry={openEntry} deleteEntry={deleteEntry} />}
            {page === "entry" && <EntryDetail entry={activeEntry} goTo={goTo} />}
          </div>
        </div>
      </div>

      <Toast message={toast} />
    </div>
  );
}
