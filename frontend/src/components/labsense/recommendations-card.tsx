"use client";

import { Sparkles } from "lucide-react";

import { useI18n } from "@/components/labsense/locale-provider";
import { getStatusAppearance, resolveStatusTone } from "@/lib/status-appearance";
import type { Recommendation, RiskStatus } from "@/lib/types";

interface RecommendationsCardProps {
  items: Recommendation[];
  riskStatus?: RiskStatus | null;
  extractionIssue?: boolean;
  limited?: boolean;
}

export function RecommendationsCard({ items, riskStatus, extractionIssue = false, limited = false }: RecommendationsCardProps) {
  const { messages } = useI18n();
  const appearance = getStatusAppearance(resolveStatusTone(riskStatus, extractionIssue || limited));

  if (!items.length) {
    return (
      <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-5 shadow-panel md:p-7">
        <h3 className="inline-flex items-center gap-2 text-lg font-semibold text-[var(--foreground)]">
          <Sparkles className="h-4 w-4" />
          {messages.recommendationsCard.title}
        </h3>
        <p className="mt-4 rounded-[1.4rem] bg-[var(--background)] p-4 text-sm leading-6 text-[var(--muted-foreground)]">
          {messages.recommendationsCard.empty}
        </p>
      </article>
    );
  }

  return (
    <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-5 shadow-panel md:p-7">
      <h3 className="inline-flex items-center gap-2 text-lg font-semibold text-[var(--foreground)]">
        <Sparkles className="h-4 w-4" />
        {messages.recommendationsCard.title}
      </h3>
      <ul className="mt-5 space-y-3">
        {items.map((item, index) => (
          <li key={item.title} className={`rounded-[1.4rem] border p-4 ${index === 0 ? appearance.panel : "border-[var(--border)] bg-[var(--background)]/55"}`}>
            <div className="flex items-start gap-3">
              <span className={`inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-semibold ${appearance.badge}`}>
                {index + 1}
              </span>
              <div>
                <p className="text-sm font-semibold text-[var(--foreground)]">{item.title}</p>
                <p className="mt-1 text-sm leading-6 text-[var(--muted-foreground)]">{item.detail}</p>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </article>
  );
}
