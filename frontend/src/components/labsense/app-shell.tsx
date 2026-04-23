import type { ReactNode } from "react";

import { AppNav } from "@/components/labsense/app-nav";
import { LanguageToggle } from "@/components/labsense/language-toggle";
import { ThemeToggle } from "@/components/labsense/theme-toggle";

interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-[var(--background)]">
      <AppNav />
      <div className="mx-auto hidden w-full max-w-6xl items-center justify-end gap-2 px-8 pt-5 md:flex">
        <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--card)] px-2 py-2 shadow-panel">
          <LanguageToggle />
          <ThemeToggle />
        </div>
      </div>
      <div className="mx-auto flex w-full items-center justify-end gap-2 px-4 pt-4 md:hidden">
        <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--card)] px-2 py-2 shadow-panel">
          <LanguageToggle />
          <ThemeToggle />
        </div>
      </div>
      {children}
    </div>
  );
}
