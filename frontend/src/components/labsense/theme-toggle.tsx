"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

import { useI18n } from "@/components/labsense/locale-provider";

export function ThemeToggle() {
  const [dark, setDark] = useState(false);
  const { messages } = useI18n();

  useEffect(() => {
    const saved = window.localStorage.getItem("labsense-theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const shouldUseDark = saved ? saved === "dark" : prefersDark;
    setDark(shouldUseDark);
    document.documentElement.classList.toggle("dark", shouldUseDark);
  }, []);

  function toggleTheme() {
    const next = !dark;
    setDark(next);
    window.localStorage.setItem("labsense-theme", next ? "dark" : "light");
    document.documentElement.classList.toggle("dark", next);
  }

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--card)] px-3 py-1.5 text-xs text-[var(--muted-foreground)]"
      aria-label={messages.common.theme}
    >
      {dark ? <Moon className="h-3.5 w-3.5" /> : <Sun className="h-3.5 w-3.5" />}
      {dark ? messages.common.dark : messages.common.light}
    </button>
  );
}
