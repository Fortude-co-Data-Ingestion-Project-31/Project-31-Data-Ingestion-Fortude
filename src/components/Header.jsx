import React from "react";
import { Menu, Bell, Settings, Moon, Sun } from "lucide-react";
import { COLORS } from "../theme";

// The top header bar provides the app title actions and the menu button for the sidebar.
export default function Header({ notificationCount = 3, onToggleSidebar, onOpenSettings = () => {}, themeMode = "light", onToggleTheme = () => {} }) {
  return (
    <div
      className="flex items-center justify-between px-8"
      style={{ height: 64, background: COLORS.header, borderBottom: `1px solid ${COLORS.border}` }}
    >
      <button
        type="button"
        onClick={onToggleSidebar}
        className="rounded-md p-2 transition-colors hover:bg-slate-100"
        aria-label="Toggle sidebar navigation"
      >
        <Menu size={20} style={{ color: COLORS.textMuted }} />
      </button>

      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={onToggleTheme}
          className="rounded-md p-2 transition-colors hover:bg-slate-100"
          aria-label="Toggle dark mode"
        >
          {themeMode === "dark" ? (
            <Sun size={18} style={{ color: COLORS.textMuted }} />
          ) : (
            <Moon size={18} style={{ color: COLORS.textMuted }} />
          )}
        </button>
        <div className="relative cursor-pointer">
          <Bell size={19} style={{ color: COLORS.textMuted }} />
          {notificationCount > 0 && (
            <span
              className="absolute flex items-center justify-center text-white rounded-full"
              style={{ top: -6, right: -7, width: 16, height: 16, fontSize: 10, background: COLORS.blue, fontWeight: 600 }}
            >
              {notificationCount}
            </span>
          )}
        </div>
        <Settings size={19} style={{ color: COLORS.textMuted }} className="cursor-pointer" onClick={onOpenSettings} />
      </div>
    </div>
  );
}
