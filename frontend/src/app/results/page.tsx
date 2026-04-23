"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useI18n } from "@/components/labsense/locale-provider";
import { AbnormalMarkersCard } from "@/components/labsense/abnormal-markers-card";
import { AnalysisSummaryCard } from "@/components/labsense/analysis-summary-card";
import { DisclaimerNote } from "@/components/labsense/disclaimer-note";
import { InterpretationCard } from "@/components/labsense/interpretation-card";
import { PageShell } from "@/components/labsense/page-shell";
import { RecommendationsCard } from "@/components/labsense/recommendations-card";
import { readAnalysisSession, readAnalysisSessionLocale } from "@/lib/analysis-session";
import { buildMarkerRenderingState } from "@/lib/marker-rendering";
import { buildSummaryMessaging } from "@/lib/analysis-transform";
import type { AnalysisSessionData } from "@/lib/types";

export default function ResultsPage() {
  const { locale, messages, setLocale } = useI18n();
  const [result, setResult] = useState<AnalysisSessionData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const sessionLocale = readAnalysisSessionLocale();
    const data = readAnalysisSession();
    if (data && sessionLocale && sessionLocale !== locale) {
      setLocale(sessionLocale);
    }
    setResult(data);
    setLoading(false);
  }, [locale, setLocale]);

  if (loading) {
    return (
      <PageShell title={messages.results.title} subtitle={messages.results.loadingSubtitle}>
        <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-6 text-sm leading-6 text-[var(--muted-foreground)] shadow-panel">
          {messages.results.loadingBody}
        </article>
      </PageShell>
    );
  }

  if (!result) {
    return (
      <PageShell title={messages.results.title} subtitle={messages.results.emptySubtitle}>
        <article className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-6 shadow-panel">
          <p className="text-sm leading-6 text-[var(--muted-foreground)]">
            {messages.results.emptyBody}
          </p>
          <Link
            href="/upload"
            className="mt-5 inline-flex rounded-full bg-[var(--foreground)] px-5 py-3 text-sm font-medium text-[var(--background)]"
          >
            {messages.results.emptyCta}
          </Link>
        </article>
      </PageShell>
    );
  }

  const localizedSummary = {
    ...result.summary,
    ...buildSummaryMessaging({
      extractedCount: result.parseMeta.extractedCount,
      warnings: result.parseMeta.warnings,
      markers: result.markers,
      riskStatus: result.riskStatus,
      locale,
      extractionIssue: result.parseMeta.extractionIssue,
      decisionKind: result.parseMeta.decisionKind,
      overviewText: result.summary.overview,
      confidenceText: result.summary.confidence
    })
  };
  const markerRendering = buildMarkerRenderingState({
    markers: result.markers,
    abnormalMarkers: result.abnormalMarkers
  });

  return (
    <PageShell title={messages.results.title} subtitle={messages.results.subtitle}>
      <AnalysisSummaryCard summary={localizedSummary} riskStatus={result.riskStatus} parseMeta={result.parseMeta} />
      <InterpretationCard
        interpretation={result.interpretation}
        riskStatus={result.riskStatus}
        extractionIssue={result.parseMeta.extractionIssue}
        limited={result.parseMeta.decisionKind === "limited"}
      />
      <RecommendationsCard
        items={result.recommendations}
        riskStatus={result.riskStatus}
        extractionIssue={result.parseMeta.extractionIssue}
        limited={result.parseMeta.decisionKind === "limited"}
      />
      <AbnormalMarkersCard
        markers={markerRendering.markers}
        allMarkersCount={markerRendering.allMarkersCount}
        extractionIssue={result.parseMeta.extractionIssue}
      />
      <DisclaimerNote />
    </PageShell>
  );
}
