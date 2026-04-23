"use client";

import { FileText } from "lucide-react";

import { useI18n } from "@/components/labsense/locale-provider";
import { parseInterpretationSections, type InterpretationSectionKey } from "@/lib/interpretation-sections";
import { getStatusAppearance, resolveStatusTone } from "@/lib/status-appearance";
import type { InterpretationState, RiskStatus } from "@/lib/types";

interface InterpretationCardProps {
  interpretation: InterpretationState;
  riskStatus?: RiskStatus | null;
  extractionIssue?: boolean;
  limited?: boolean;
}

const hiddenSectionKeys = new Set<InterpretationSectionKey>(["nextSteps", "optionalImprovements"]);

export function InterpretationCard({ interpretation, riskStatus, extractionIssue = false, limited = false }: InterpretationCardProps) {
  const { messages } = useI18n();
  const appearance = getStatusAppearance(resolveStatusTone(riskStatus, extractionIssue || limited));

  if (interpretation.status !== "ready") {
    return (
      <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-5 shadow-panel md:p-7">
        <h3 className="inline-flex items-center gap-2 text-lg font-semibold text-[var(--foreground)]">
          <FileText className="h-4 w-4" />
          {messages.interpretationCard.title}
        </h3>
        <p className="mt-4 rounded-[1.4rem] bg-[var(--background)] p-4 text-sm leading-6 text-[var(--muted-foreground)]">
          {interpretation.error ?? messages.interpretationCard.unavailable}
        </p>
      </article>
    );
  }

  const localizedTitles: Record<InterpretationSectionKey, string> = messages.interpretationCard.sections;
  const sections = parseInterpretationSections(interpretation.text).filter(
    (section) => !section.key || !hiddenSectionKeys.has(section.key)
  );

  return (
    <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-5 shadow-panel md:p-7">
      <h3 className="inline-flex items-center gap-2 text-lg font-semibold text-[var(--foreground)]">
        <FileText className="h-4 w-4" />
        {messages.interpretationCard.title}
      </h3>
      <div className="mt-5 space-y-4">
        {sections.map((section, index) => (
          <section
            key={`${section.key ?? "body"}-${index}`}
            className={
              index === 0
                ? `rounded-[1.5rem] border p-4 ${appearance.panel}`
                : "rounded-[1.4rem] border border-[var(--border)] bg-[var(--background)]/55 p-4"
            }
          >
            {section.key ? (
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--muted-foreground)]">
                {localizedTitles[section.key]}
              </p>
            ) : null}
            <div className="mt-2 space-y-2 text-sm leading-6 text-[var(--foreground)]">
              {section.lines.map((line) => (
                <p key={line}>{line}</p>
              ))}
            </div>
          </section>
        ))}
      </div>
    </article>
  );
}
