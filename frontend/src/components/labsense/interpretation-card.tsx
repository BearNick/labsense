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

export function InterpretationCard({ interpretation, riskStatus, extractionIssue = false, limited = false }: InterpretationCardProps) {
  const { messages } = useI18n();
  const appearance = getStatusAppearance(resolveStatusTone(riskStatus, extractionIssue || limited));
  const sections = parseInterpretationSections(interpretation.text);

  if (interpretation.status !== "ready") {
    return (
      <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-5 shadow-panel md:p-7">
        <h2 className="inline-flex items-center gap-2 text-lg font-semibold text-[var(--foreground)]">
          <FileText className="h-4 w-4" />
          {messages.interpretationCard.title}
        </h2>
        <p className="bg-theme-subtle text-theme-body mt-4 rounded-[1.4rem] p-4 text-sm leading-6 dark:bg-[var(--background)]">
          {interpretation.error ?? messages.interpretationCard.unavailable}
        </p>
      </article>
    );
  }

  return (
    <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-5 shadow-panel md:p-7">
      <h2 className="inline-flex items-center gap-2 text-lg font-semibold text-[var(--foreground)]">
        <FileText className="h-4 w-4" />
        {messages.interpretationCard.title}
      </h2>
      <div className={`mt-5 rounded-[1.5rem] border p-4 ${appearance.panel}`}>
        <div className="space-y-5 text-sm leading-6 text-[var(--foreground)]">
          {sections.map((section, index) => {
            if (!section.key) {
              return (
                <div key={`freeform-${index}`} className="space-y-2">
                  {section.lines.map((line, lineIndex) => (
                    <p key={`freeform-line-${lineIndex}`}>{line}</p>
                  ))}
                </div>
              );
            }

            return (
              <section key={`${section.key}-${index}`} className="space-y-2.5">
                <h3 className={getSectionHeadingClassName(section.key)}>
                  {messages.interpretationCard.sections[section.key]}
                </h3>
                <div className="space-y-2.5">
                  {section.key === "keyObservations"
                    ? section.lines.map((line, lineIndex) => {
                        const detail = splitObservationLine(line);
                        if (!detail) {
                          return <p key={`observation-${lineIndex}`}>{line}</p>;
                        }

                        return (
                          <div key={`observation-${lineIndex}`} className="space-y-1">
                            <p className="text-[0.8rem] font-semibold uppercase tracking-[0.14em] text-[var(--text-secondary)]">
                              {detail.label}
                            </p>
                            <p>{detail.content}</p>
                          </div>
                        );
                      })
                    : section.lines.map((line, lineIndex) => <p key={`section-line-${lineIndex}`}>{line}</p>)}
                </div>
              </section>
            );
          })}
        </div>
      </div>
    </article>
  );
}

function getSectionHeadingClassName(key: InterpretationSectionKey): string {
  if (key === "keyObservations") {
    return "text-[0.8rem] font-semibold uppercase tracking-[0.14em] text-[var(--text-secondary)]";
  }

  return "text-[0.92rem] font-semibold tracking-[0.01em] text-[var(--foreground)]";
}

function splitObservationLine(line: string): { label: string; content: string } | null {
  const separatorIndex = line.indexOf(":");
  if (separatorIndex <= 0) {
    return null;
  }

  const label = line.slice(0, separatorIndex).trim();
  const content = line.slice(separatorIndex + 1).trim();
  if (!label || !content) {
    return null;
  }

  return { label, content };
}
