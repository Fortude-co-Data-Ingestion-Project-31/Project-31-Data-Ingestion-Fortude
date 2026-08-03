import React from "react";
import { Menu, Bell, Settings } from "lucide-react";
import { COLORS } from "../theme";

export default function Header({ notificationCount = 3 }) {
  return (
    <div
      className="flex items-center justify-between px-8"
      style={{ height: 64, background: COLORS.header, borderBottom: `1px solid ${COLORS.border}` }}
    >
      <Menu size={20} style={{ color: COLORS.textMuted }} className="cursor-pointer" />
      <div className="flex items-center gap-5">
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
        <Settings size={19} style={{ color: COLORS.textMuted }} className="cursor-pointer" />
      </div>
    </div>
  );
}
