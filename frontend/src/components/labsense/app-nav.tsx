"use client";

import Link from "next/link";
import type { Route } from "next";
import { usePathname } from "next/navigation";
import { CircleUserRound, Clock4, House, Microscope, Upload } from "lucide-react";
import type { ComponentType } from "react";

import { LabsenseBrand } from "@/components/labsense/brand-mark";
import { useI18n } from "@/components/labsense/locale-provider";
import { cn } from "@/lib/utils";

const linkMeta: Array<{ href: Route; key: "landing" | "upload" | "results" | "history" | "account"; icon: ComponentType<{ className?: string }> }> = [
  { href: "/", key: "landing", icon: House },
  { href: "/upload", key: "upload", icon: Upload },
  { href: "/results", key: "results", icon: Microscope },
  { href: "/history", key: "history", icon: Clock4 },
  { href: "/account", key: "account", icon: CircleUserRound }
];

export function AppNav() {
  const pathname = usePathname();
  const { messages } = useI18n();
  const links = linkMeta.map((link) => ({
    ...link,
    label: messages.nav[link.key]
  }));

  return (
    <>
      <header className="sticky top-0 z-30 hidden border-b border-[var(--border)] bg-[color:var(--surface)]/88 backdrop-blur md:block">
        <div className="mx-auto flex h-[72px] max-w-6xl items-center justify-between px-8 py-3">
          <LabsenseBrand />
          <nav className="rounded-full border border-[var(--border)] bg-[var(--card)] p-1 shadow-panel">
            <div className="flex items-center gap-1">
            {links.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "rounded-full px-4 py-2 text-sm font-medium transition",
                    active
                      ? "bg-[var(--foreground)] text-[var(--background)] shadow-sm"
                      : "text-[var(--muted-foreground)] hover:bg-[var(--secondary)] hover:text-[var(--foreground)]"
                  )}
                >
                  {link.label}
                </Link>
              );
            })}
            </div>
          </nav>
        </div>
      </header>

      <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-[var(--border)] bg-[color:var(--surface)]/94 px-3 pb-[max(env(safe-area-inset-bottom),0.65rem)] pt-3 backdrop-blur md:hidden">
        <ul className="mx-auto grid max-w-2xl grid-cols-5 gap-2 rounded-[1.6rem] border border-[var(--border)] bg-[var(--card)] p-2 shadow-panel">
          {links.map((link) => {
            const active = pathname === link.href;
            const Icon = link.icon;
            return (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className={cn(
                    "flex min-h-[62px] flex-col items-center justify-center gap-1 rounded-2xl px-1 py-2 text-[11px] font-medium transition",
                    active
                      ? "bg-[var(--foreground)] text-[var(--background)] shadow-sm"
                      : "text-[var(--muted-foreground)]"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{link.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </>
  );
}
