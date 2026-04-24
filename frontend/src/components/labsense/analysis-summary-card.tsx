"use client";

import { Activity, AlertCircle, ShieldAlert, ShieldCheck } from "lucide-react";

import { useI18n } from "@/components/labsense/locale-provider";
import { getMessages, type Locale } from "@/lib/i18n";
import { getStatusAppearance, resolveStatusTone, type StatusTone } from "@/lib/status-appearance";
import type { AnalysisSummary, RiskStatus } from "@/lib/types";

interface AnalysisSummaryCardProps {
  summary: AnalysisSummary;
  riskStatus?: RiskStatus | null;
  reportLanguage: Locale;
  eyebrow?: string;
  parseMeta: {
    source: string;
    extractedCount: number;
    warnings: string[];
    extractionIssue: boolean;
    confidenceScore: number | null;
    confidenceLevel: "high" | "medium" | "low" | null;
    confidenceExplanation: string | null;
    decisionKind: "full" | "limited" | "extraction_issue";
    statusLabel: string | null;
    statusExplanation: string | null;
    hideMarkerCounts: boolean;
    hidePriorityNotes: boolean;
    recommendedAction: string | null;
  };
}

function resolveProcessingSource(source: string, messages: ReturnType<typeof useI18n>["messages"]): string {
  if (source === "demo") return messages.common.sourceDemo;
  if (source === "vision") return messages.common.sourceVision;
  if (source === "pdfplumber") return messages.common.sourcePdfplumber;
  return source;
}

function StatusIcon({ tone }: { tone: StatusTone }) {
  if (tone === "normal") return <ShieldCheck className="h-5 w-5" />;
  if (tone === "borderline") return <Activity className="h-5 w-5" />;
  if (tone === "critical") return <AlertCircle className="h-5 w-5" />;
  return <ShieldAlert className="h-5 w-5" />;
}

export function AnalysisSummaryCard({ summary, riskStatus, reportLanguage, eyebrow, parseMeta }: AnalysisSummaryCardProps) {
  const { messages } = useI18n();
  const reportMessages = getMessages(reportLanguage);
  const extractionIssue = parseMeta.extractionIssue;
  const lowConfidence = parseMeta.decisionKind === "limited" && parseMeta.confidenceLevel === "low" && !extractionIssue;
  const tone = resolveStatusTone(riskStatus, extractionIssue || parseMeta.decisionKind === "limited");
  const appearance = getStatusAppearance(tone);
  const statusLabel =
    parseMeta.statusLabel ??
    riskStatus?.label ??
    (extractionIssue ? reportMessages.generated.extractionIssueTitle : null) ??
    reportMessages.riskStatus.green.label;
  const statusMeaning =
    parseMeta.statusExplanation ??
    riskStatus?.explanation ??
    (extractionIssue ? reportMessages.generated.extractionIssueOverview : null) ??
    reportMessages.riskStatus.green.explanation;
  const showOverview = !(lowConfidence && summary.overview === summary.confidence);

  return (
    <article className={`h-fit overflow-hidden rounded-[2rem] border bg-[var(--card)] shadow-panel ${appearance.hero}`}>
      <div className="grid gap-4 p-5 md:p-6 xl:grid-cols-[minmax(0,1.18fr)_minmax(210px,0.82fr)] xl:gap-5 xl:p-7">
        <div className="min-w-0">
          <p className="text-theme-muted text-xs uppercase tracking-[0.16em]">
            {eyebrow ?? messages.summaryCard.eyebrow}
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <span className={`inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl ${appearance.iconWrap}`}>
              <StatusIcon tone={tone} />
            </span>
            <div className="min-w-0">
              <div className={`inline-flex items-center rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] ${appearance.badge}`}>
                {statusLabel}
              </div>
              <h2 className="text-theme-heading mt-3 text-[1.75rem] font-semibold leading-tight tracking-[-0.04em] text-balance md:text-[2rem] xl:text-[2.15rem]">
                {summary.title}
              </h2>
            </div>
          </div>
          <p className="text-theme-body mt-4 max-w-2xl text-sm leading-6">{statusMeaning}</p>
          {showOverview ? <p className="text-theme-muted mt-3 max-w-2xl text-sm leading-6">{summary.overview}</p> : null}
        </div>
        <div className={`self-start rounded-[1.6rem] border p-4 md:p-5 ${appearance.panel}`}>
          {extractionIssue ? (
            <p className="text-theme-body text-sm leading-6">{summary.confidence}</p>
          ) : (
            <div className="flex flex-wrap items-start gap-2">
              <div className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${appearance.badge}`}>
                <ShieldCheck className="mr-2 h-3.5 w-3.5" />
                {summary.confidence}
              </div>
            </div>
          )}
          {!parseMeta.hidePriorityNotes && !extractionIssue && riskStatus?.priority_notes.length ? (
            <ul className="text-theme-body mt-4 space-y-2 text-sm leading-6">
              {riskStatus.priority_notes.map((note) => (
                <li key={note} className="flex items-start gap-3">
                  <span className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${appearance.accent}`} />
                  <span>{note}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </div>
      <div className="border-t border-[var(--border)]/80 px-5 py-4 md:px-6 xl:px-7">
        <div className="text-theme-body grid gap-x-4 gap-y-2 text-sm sm:grid-cols-2">
          <p className="min-w-0">
            <span className="text-theme-heading font-medium">{messages.common.captured}:</span>{" "}
            <span className="whitespace-nowrap">{summary.capturedAt}</span>
          </p>
          <p className="min-w-0">
            <span className="text-theme-heading font-medium">{messages.common.source}:</span> {summary.labSource}
          </p>
          <p className="min-w-0">
            <span className="text-theme-heading font-medium">{messages.common.processing}:</span> {resolveProcessingSource(parseMeta.source, messages)}
          </p>
          {!parseMeta.hideMarkerCounts ? (
            <p className="min-w-0">
              <span className="text-theme-heading font-medium">{messages.common.markersExtracted}:</span> {parseMeta.extractedCount}
            </p>
          ) : null}
        </div>
      </div>
      {parseMeta.warnings.length && !parseMeta.extractionIssue ? (
        <div className="px-5 pb-5 md:px-7 md:pb-7">
          <p className="rounded-2xl border border-[color:var(--status-borderline-border)] bg-[color:var(--status-borderline-surface)] px-4 py-3 text-sm text-[color:var(--status-borderline-strong)]">
            {parseMeta.warnings[0]}
          </p>
        </div>
      ) : null}
    </article>
  );
}
