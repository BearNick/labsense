"use client";

import { Clock3 } from "lucide-react";
import { useEffect, useState } from "react";

import { useI18n } from "@/components/labsense/locale-provider";
import { PageShell } from "@/components/labsense/page-shell";
import { getMockHistory } from "@/lib/mock-api";
import type { HistoryItem } from "@/lib/types";

export default function HistoryPage() {
  const { locale, messages } = useI18n();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      const items = await getMockHistory(locale);
      if (!active) return;
      setHistory(items);
      setLoading(false);
    }

    void load();
    return () => {
      active = false;
    };
  }, [locale]);

  return (
    <PageShell title={messages.history.title} subtitle={messages.history.subtitle}>
      {loading ? (
        <article className="rounded-3xl border border-[var(--border)] bg-[var(--card)] p-6 text-sm text-[var(--muted-foreground)] shadow-panel">
          {messages.history.loading}
        </article>
      ) : (
        <>
          <article className="rounded-3xl border border-[var(--border)] bg-[var(--card)] p-5 text-sm text-[var(--foreground)] shadow-panel">
            <p className="leading-6 text-[var(--muted-foreground)]">{messages.history.previewNotice}</p>
          </article>

          <section className="space-y-3">
            {history.map((item) => (
              <article
                key={item.id}
                className="rounded-2xl border border-[var(--border)] bg-[var(--card)] p-4 shadow-panel"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-semibold text-[var(--foreground)]">{item.id}</p>
                    <span className="rounded-full bg-[var(--secondary)] px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.08em] text-[var(--muted-foreground)]">
                      {messages.history.exampleLabel}
                    </span>
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-1 text-xs ${item.status === "ready" ? "bg-[color:var(--success-soft)] text-[color:var(--success-strong)]" : "bg-[color:var(--warning-soft)] text-[color:var(--warning-strong)]"}`}
                  >
                    {item.status === "ready" ? messages.history.ready : messages.history.processing}
                  </span>
                </div>
                <p className="mt-2 text-sm text-[var(--muted-foreground)]">{item.date}</p>
                <p className="mt-1 text-sm text-[var(--foreground)]">{item.highlights}</p>
              </article>
            ))}
          </section>

          <p className="inline-flex items-center gap-2 text-xs text-[var(--muted-foreground)]">
            <Clock3 className="h-3.5 w-3.5" />
            {messages.history.footnote}
          </p>
        </>
      )}
    </PageShell>
  );
}
