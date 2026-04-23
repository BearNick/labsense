"use client";

import { Info } from "lucide-react";
import { useState } from "react";

import { useI18n } from "@/components/labsense/locale-provider";

interface DisclaimerNoteProps {
  compact?: boolean;
}

export function DisclaimerNote({ compact = false }: DisclaimerNoteProps) {
  const { messages } = useI18n();
  const [open, setOpen] = useState(false);

  return (
    <article className="rounded-[1.6rem] border border-[var(--border)] bg-[var(--card)] p-4 shadow-panel">
      <div className="flex items-start gap-3">
        <span className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--secondary)] text-[var(--foreground)]">
          <Info className="h-4 w-4" />
        </span>
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
            {messages.disclaimer.title}
          </p>
          <p className={`mt-2 text-sm leading-6 text-[var(--foreground)] ${compact ? "max-w-2xl" : "max-w-3xl"}`}>
            {messages.disclaimer.short}
          </p>
          <button
            type="button"
            onClick={() => setOpen((value) => !value)}
            className="mt-3 text-sm font-medium text-[var(--foreground)] underline decoration-[var(--border)] underline-offset-4"
          >
            {open ? messages.disclaimer.collapse : messages.disclaimer.expand}
          </button>
          {open ? (
            <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--muted-foreground)]">
              {messages.disclaimer.full}
            </p>
          ) : null}
        </div>
      </div>
    </article>
  );
}
